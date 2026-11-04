"""Reuse candidate-request builder; prepare graph metadata only, no server calls."""
import ast,hashlib,json
from pathlib import Path
B=Path(__file__).resolve().parent
original=B/'prepare_sampling_AB_candidate_request_v1.py'
source=original.read_text(encoding='utf-8')
replacements=[
("O=B/'sampling_model_AB_foldC_seed0_20261103_v1';F=O/'post_V1_training_freeze_audit_v2'","O=B/'blue_noise_model_pair_foldC_seed0_20261104_v1/first_training_request_v2';F=O/'post_Euclidean_training_freeze_audit_v1'"),
("C=O/'Morton_training_request_v1'","C=O/'surface_graph_training_request_v1'"),
('audit_report_v2.json','audit_report_v1.json'),("len(audit['checks'])==38","len(audit['checks'])==39"),
('V1_training_entry_request_v1.json','Euclidean_training_entry_request_v1.json'),
('V1_training_execution_request_v2.json','Euclidean_training_execution_request_v1.json'),
('4a889afad90b1a8a52fcb75691c71990d03af8b7d120a96608ac4b9b85cb7a62','40a45089ed847261d9477993118b406048dadd09d15e492a402b455bddfdad74'),
('BCSP_SAMPLING_AB_V1','BCSP_BLUE_NOISE_AB_V1'),('bcsp-sampling-','bcsp-blue-noise-'),
('control_Morton_v1','control_surface_graph_v1'),('Morton_area_stratified8k','surface_graph'),
('bcsp_sampling_ab_foldC_Morton_in8192_out8192_seed0_train_v1','bcsp_blue_noise_foldC_surface_graph_in8192_out8192_seed0_train_v1'),
('bcsp_sampling_ab_foldc_morton_control_v1','bcsp_blue_noise_ab_foldc_graph_control_v1'),
('bcsp_sampling_ab_foldc_morton_seed0_train_v1','bcsp_blue_noise_foldc_graph_seed0_train_v1'),
("O/'qualified_V1_training_receipt_v1.json'","O/'evidence/qualified_Euclidean_training_receipt_v1.json'"),
("'already_installed_and_stream_hash_verified':True","'installed_hash_verified_at_initial_deployment':True,'post_baseline_audit_stream_rehashed':False"),
("'no V1 retraining'","'no Euclidean baseline retraining'"),
('never load final V1 weights','never load final Euclidean weights'),
('no baseline checkpoint load/resume','no baseline checkpoint load/resume'),
]
for old,new in replacements:
    assert old in source,old
    source=source.replace(old,new)
ast.parse(source)
exec(compile(source,str(original)+'[blue-graph-request]','exec'),{'__file__':str(original),'__name__':'__main__'})
