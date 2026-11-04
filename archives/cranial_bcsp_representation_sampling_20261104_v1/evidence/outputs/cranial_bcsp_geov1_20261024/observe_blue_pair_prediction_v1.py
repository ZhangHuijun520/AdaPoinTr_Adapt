"""Reuse bounded read-only observation for the authorized blue-noise pair."""
from pathlib import Path
p=Path(__file__).resolve().with_name('observe_sampling_pair_prediction_v1.py')
s=p.read_text(encoding='utf-8').replace('sampling_model_AB_foldC_seed0_20261103_v1/paired_development_eval_v1','blue_pair_eval_v1')
exec(compile(s,str(p)+'[blue-pair-observe]','exec'),{'__file__':str(p),'__name__':'__main__'})
