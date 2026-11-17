"""Prepare local P3 and pending transport from the single passed CPU batch."""
from pathlib import Path
import ast
S=Path(__file__).resolve().parent;P=S/'G1_C_implementation_v1';V=S/'G2_C_implementation_v1'
s=(P/'freeze_G1_C_P3_request_v1.py').read_text(encoding='utf-8').replace('G1','G2')
s=s.replace("cpu['count']==16", "cpu['count']==24").replace('CPU_checks=16','CPU_checks=24')
s=s.replace("p3=dict(status=", "global_baseline=S/'G1_C_implementation_v1/post_training_freeze_v1/formal_freeze_result_v1.json';gb=read(global_baseline);assert gb['status']=='FORMAL_SPCG_G1_C_POST_TRAINING_FREEZE_PASS' and all(gb['checks'].values()) and q['G1_C_freeze']==rec(global_baseline,root+'/G1_C_formal_training_freeze_v1.json')\n p3=dict(status=")
s=s.replace('G0_C_freeze=rec(baseline),', 'G0_C_freeze=rec(baseline),G1_C_freeze=rec(global_baseline),')
s=s.replace('G0_same_fold_order_and_counts_required=True,', 'G0_same_fold_order_and_counts_required=True,G1_same_head_initialization_and_order_required=True,actual_k8_route_and_direct_Q_CPU=True,full_authorize_actual_metadata_CPU=True,actual_optimizer_group_function_CPU=True,')
s=s.replace('OnlyG2_C now supported; G2/D remain separately scoped.', 'OnlyG2_C now supported; D fold remains separately scoped.')
s=s.replace("q['G0_C_freeze']['path']:baseline,", "q['G0_C_freeze']['path']:baseline,q['G1_C_freeze']['path']:global_baseline,")
s=s.replace("paired_G0_freeze_exact=True,", "paired_G0_freeze_exact=True,paired_G1_freeze_exact=True,")
s=s.replace("baseline,V/'final_request_static_review_v1.json'", "baseline,global_baseline,V/'final_request_static_review_v1.json'")
s=s.replace("'G0_C_formal_training_freeze_v3.json' if p==baseline else p.name", "'G0_C_formal_training_freeze_v3.json' if p==baseline else 'G1_C_formal_training_freeze_v1.json' if p==global_baseline else p.name")
s=s.replace("No G0trainedcheckpoint loaded.", "G0/G1 formal freeze proofs required. No trainedcheckpoint loaded.")
ast.parse(s)
with (V/'freeze_G2_C_P3_request_v1.py').open('x',encoding='utf-8',newline='\n') as f:f.write(s)
print('STATIC_PASS_G2_P3_DELIVERY_BUILDER')
