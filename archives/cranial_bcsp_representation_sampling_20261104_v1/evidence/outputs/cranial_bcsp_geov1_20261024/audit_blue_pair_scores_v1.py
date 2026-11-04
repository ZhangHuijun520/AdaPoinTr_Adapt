"""Independent stdlib audit of the blue-pair saved scores, no metric rerun."""
from pathlib import Path
p=Path(__file__).resolve().with_name('audit_sampling_pair_scores_v1.py')
s=p.read_text(encoding='utf-8')
for old,new in [
('sampling_model_AB_foldC_seed0_20261103_v1/paired_development_eval_v1','blue_pair_eval_v1'),
('0748d8e99c6589e47195a255abaf58f77751941e17c71e5e6ddb7c456ff059fa','a2a24869ca8b7300e1a804359c0a542bcba8473189eaa8f28d0c5aabb9e8bbe8'),
('bcsp-sampling-pair-','bcsp-blue-noise-pair-'),
('mean_delta_Morton_minus_V1','mean_delta_graph_minus_Euclidean'),('mean_V1','mean_Euclidean'),('mean_Morton','mean_graph'),
('Nop_D_V1','Nop_D_Euclidean_elimination'),('Morton_area_stratified8k','surface_graph'),("'V1'","'Euclidean_elimination'")]:
    assert old in s,old;s=s.replace(old,new)
exec(compile(s,str(p)+'[blue-score-audit]','exec'),{'__file__':str(p),'__name__':'__main__'})
