"""Generate local P3/delivery builder; do not rerun CPU batch."""
from pathlib import Path
import ast
S=Path(__file__).resolve().parent;V=S/'G1_D_implementation_v1'
s=(S/'G1_C_implementation_v1/freeze_G1_C_P3_request_v1.py').read_text(encoding='utf-8')
for a,b in [('G1_C','G1_D'),('SPCG_G1C','SPCG_G1D'),('G0_C','G0_D'),('UTC_order_hotfix_v3/post_training_freeze_v3/formal_freeze_result_v3.json','G0_D_implementation_v1/post_training_freeze_v1/formal_freeze_result_v1.json'),('G0_D_formal_training_freeze_v3.json','G0_D_formal_training_freeze_v1.json'),('bcsp_spcg_G1_D_training_pending_20261116_v1.tar.gz','bcsp_spcg_G1_D_training_pending_20261117_v1.tar.gz'),("cpu['count']==16","cpu['count']==22"),('CPU_checks=16','CPU_checks=22'),('bridge_only_G1_arm_guard_changed=True','bridge_only_fold_guard_changed=True'),('OnlyG1_D now supported; G2/D remain separately scoped.','OnlyG1_D supported by this entry; G2_D remains separately scoped.')]:s=s.replace(a,b)
s=s.replace("inherited_training_P3=rec(S/'UTC_order_hotfix_v3/training_P3_v3.json')", "inherited_training_P3=rec(S/'G0_D_implementation_v1/training_P3_v1.json')")
s=s.replace('real_mother_forward_FC_loss_route_CPU=True,', 'real_mother_forward_FC_loss_route_CPU=True,complete_authorize_D_metadata_CPU=True,global256_aggregation_and_direct_Q_CPU=True,wrong_fold_data_order_and_parent_hash_rejected=True,actual_optimizer_groups_and_SSM_exemption_CPU=True,')
ast.parse(s)
with (V/'freeze_G1_D_P3_request_v1.py').open('x',encoding='utf-8') as f:f.write(s)
print('G1D_P3_BUILDER_STATIC_PASS')
