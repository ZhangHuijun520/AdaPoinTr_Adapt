from pathlib import Path
import ast
S=Path(__file__).resolve().parent;V=S/'G1_D_rebind_v2'
s=(S/'G1_D_implementation_v1/freeze_G1_D_P3_request_v1.py').read_text(encoding='utf-8')
s=s.replace("cpu['count']==22","cpu['count']==28").replace('CPU_checks=22','CPU_checks=28').replace('SPCG_G1_D_training_execution_request_v1.json','SPCG_G1_D_training_execution_request_v2.json').replace('bcsp_spcg_G1_D_training_pending_20261117_v1.tar.gz','bcsp_spcg_G1_D_training_pending_20261117_v2.tar.gz').replace('resources8.5GiB','resources6GiB')
s=s.replace('identity_and_order_inherited_G0=True','same_order_as_G0=True,new_identity_frozen=True,cross_device_G0_comparison_disclosed=True')
s=s.replace('new_run_paths_pending_only=True','new_run_paths_pending_only=True,startup_6GiB_boundary_CPU=True,runtime_4GiB_and_output_1GiB_unchanged=True,old_identity_and_selector_rejected_CPU=True,accepted_cross_device_limitation=True')
s=s.replace("G0_D_freeze=rec(baseline),", "G0_D_freeze=rec(baseline),resource_revision=rec(V/'revision_scope_v2.json'),")
s=s.replace("'OnlyG1_D supported by this entry; G2_D remains separately scoped.'", "'G0_D was trained on another GPU; comparisons with it are cross-device. G1_D/G2_D must use the new same-device block; no equivalence or strict same-device G0 claim.', 'Startup threshold is6GiB; runtime4GiB and output1GiB unchanged. Shared storage availability must be rechecked.', 'OnlyG1_D supported by this entry; G2_D remains separately scoped.'")
s=s.replace("baseline,V/'final_request_static_review_v1.json'", "baseline,V/'revision_scope_v2.json',V/'final_request_static_review_v1.json'")
ast.parse(s)
with (V/'freeze_G1_D_P3_request_v2.py').open('x',encoding='utf-8') as f:f.write(s)
print('DELIVERY_BUILDER_STATIC_PASS')
