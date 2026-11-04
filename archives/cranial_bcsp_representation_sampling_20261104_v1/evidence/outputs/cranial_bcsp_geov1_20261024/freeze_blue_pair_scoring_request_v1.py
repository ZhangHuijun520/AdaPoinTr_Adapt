"""Freeze one pending CPU score scope after the actual local verification/tests."""
import ast
from pathlib import Path
B=Path(__file__).resolve().parent
p=B/'freeze_sampling_pair_scoring_request_v1.py';s=p.read_text(encoding='utf-8')
for old,new in [
('sampling_model_AB_foldC_seed0_20261103_v1/paired_development_eval_v1','blue_pair_eval_v1'),
('76673ba94626253161dc70f0a33006d21c8094bced8148496c68c6c3490f0f4c','4fd0d2736e58530326c37d77fdbd5e76242339c36ea0a7905290a58d0b31ab43'),
('bcsp_sampling_pair_score_v1.py','bcsp_blue_pair_score_v1.py'),
('bcsp-sampling-pair-','bcsp-blue-noise-pair-'),
('Morton_area_stratified8k','surface_graph'),("'V1'","'Euclidean_elimination'"),
('Morton minus V1','surface_graph minus Euclidean_elimination'),('V1 vs Morton','Euclidean_elimination vs surface_graph'),
('V1／Morton','欧氏／图距离'),('Morton−V1','图距离−欧氏'),('V1输入原样','欧氏输入原样'),('Morton输入原样','图距离输入原样'),
('2026-11-03','2026-11-04'),
("parent_scorer=bind(B/'development_eval_v1/bcsp_development_score_v1.py')","parent_scorer=bind(B/'sampling_model_AB_foldC_seed0_20261103_v1/paired_development_eval_v1/score_implementation_v1/bcsp_sampling_pair_score_v1.py')")]:
    assert old in s,old;s=s.replace(old,new)
ast.parse(s)
exec(compile(s,str(p)+'[blue-pair-score]','exec'),{'__file__':str(p),'__name__':'__main__'})
