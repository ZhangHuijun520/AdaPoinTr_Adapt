from pathlib import Path
import ast
S=Path(__file__).resolve().parent;V=S/'G2_D_implementation_v1'
s=(S/'G1_D_rebind_v2/freeze_G1_D_P3_request_v2.py').read_text(encoding='utf-8').replace('G1','G2')
for a,b in [("cpu['count']==28","cpu['count']==32"),('CPU_checks=28','CPU_checks=32'),('SPCG_G2_D_training_execution_request_v2.json','SPCG_G2_D_training_execution_request_v1.json'),('bcsp_spcg_G2_D_training_pending_20261117_v2.tar.gz','bcsp_spcg_G2_D_training_pending_20261117_v1.tar.gz'),('revision_scope_v2.json','implementation_scope_v1.json'),('global256_aggregation_and_direct_Q_CPU=True','local8_aggregation_and_direct_Q_CPU=True'),('bridge_only_fold_guard_changed=True','bridge_only_arm_guard_changed=True'),('G2_D/G2_D','G1_D/G2_D'),('OnlyG2_D supported by this entry; G2_D remains separately scoped.','OnlyG2_D supported by this entry; future prediction/evaluation remains separately scoped.'),("inherited_training_P3=rec(S/'G0_D_implementation_v1/training_P3_v1.json')","inherited_training_P3=rec(S/'G1_D_rebind_v2/training_P3_v1.json')")]:s=s.replace(a,b)
line=" for p in [entry,bridge,test,Path(__file__)]:"
s=s.replace(line," paired=S/'G1_D_rebind_v2/post_training_freeze_v2/formal_freeze_result_v2.json';gp=read(paired);assert gp['status']=='FORMAL_SPCG_G1_D_POST_TRAINING_FREEZE_PASS' and all(gp['checks'].values()) and q['G1_D_freeze']==rec(paired,root+'/G1_D_formal_training_freeze_v2.json')\n"+line)
s=s.replace('G0_D_freeze=rec(baseline),','G0_D_freeze=rec(baseline),G1_D_freeze=rec(paired),')
s=s.replace('accepted_cross_device_limitation=True','accepted_cross_device_limitation=True,G1_D_same_device_and_full_initial_state_required=True,G1_D_wrong_proof_hash_or_device_rejected_CPU=True,G2_memory_global_gradients_finite_CPU=True')
s=s.replace("q['G0_D_freeze']['path']:baseline,","q['G0_D_freeze']['path']:baseline,q['G1_D_freeze']['path']:paired,")
s=s.replace("for p in [entry,bridge,test,V/'CPU_scope_v1.json',V/'CPU_batch_v1/result.json',V/'training_P3_v1.json',baseline,", "for p in [entry,bridge,test,V/'CPU_scope_v1.json',V/'CPU_batch_v1/result.json',V/'training_P3_v1.json',baseline,paired,")
s=s.replace("'G0_D_formal_training_freeze_v1.json' if p==baseline else p.name", "'G0_D_formal_training_freeze_v1.json' if p==baseline else 'G1_D_formal_training_freeze_v2.json' if p==paired else p.name")
s=s.replace('same_order_as_G0=True,','same_order_as_G0=True,G1_D_same_device_and_init_bound=True,')
ast.parse(s)
with (V/'freeze_G2_D_P3_request_v1.py').open('x',encoding='utf-8') as f:f.write(s)
print('G2D_P3_BUILDER_STATIC_PASS')
