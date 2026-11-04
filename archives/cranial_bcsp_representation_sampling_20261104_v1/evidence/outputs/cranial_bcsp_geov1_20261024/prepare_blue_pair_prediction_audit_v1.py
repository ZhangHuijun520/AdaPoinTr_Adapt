"""Bind the established210-prediction read-only audit to the blue-noise pair."""
import ast
from pathlib import Path
B=Path(__file__).resolve().parent
p=B/'prepare_sampling_pair_prediction_audit_v1.py';s=p.read_text(encoding='utf-8')
replacements=[
('sampling_model_AB_foldC_seed0_20261103_v1/paired_development_eval_v1','blue_pair_eval_v1'),
('76673ba94626253161dc70f0a33006d21c8094bced8148496c68c6c3490f0f4c','4fd0d2736e58530326c37d77fdbd5e76242339c36ea0a7905290a58d0b31ab43'),
('prediction_observation_02_result.json','prediction_observation_2_result.json'),
('bcsp-sampling-pair-','bcsp-blue-noise-pair-'),
('C_Morton_area_stratified8k','C_surface_graph'),('C_V1','C_Euclidean_elimination'),
("a['arm']=='V1'","a['arm']=='Euclidean_elimination'"),
("b['arm']=='Morton_area_stratified8k'","b['arm']=='surface_graph'"),
('SAMPLING_PAIR_210_FORWARD_COMPLETE','BLUE_NOISE_PAIR_210_FORWARD_COMPLETE')]
for old,new in replacements:
    assert old in s,old;s=s.replace(old,new)
ast.parse(s)
exec(compile(s,str(p)+'[blue-pair-audit]','exec'),{'__file__':str(p),'__name__':'__main__'})
for original,target in [('invoke_sampling_pair_prediction_audit_v1.py','invoke_blue_pair_prediction_audit_v1.py'),('finalize_sampling_pair_prediction_audit_v1.py','finalize_blue_pair_prediction_audit_v1.py')]:
    text=(B/original).read_text(encoding='utf-8').replace(replacements[0][0],replacements[0][1])
    if target.startswith('finalize'):
        text=text.replace('BCSP_SAMPLING_AB_V1','BCSP_BLUE_NOISE_AB_V1').replace('2026-11-03_paired_development_eval','2026-11-04_paired_development_eval').replace('C_Morton_area_stratified8k','C_surface_graph').replace('C_V1','C_Euclidean_elimination').replace('V1／Morton','欧氏／图距离').replace('Morton优于V1','图距离优于欧氏')
    ast.parse(text)
    with (B/target).open('x',encoding='utf-8') as f:f.write(text)
print('BLUE_PAIR_FORMAL_AUDIT_STATIC_PASS_NO_SERVER_CALLS')
