"""Bind the existing single-attempt local runner to the explicit blue-pair grant."""
from pathlib import Path
p=Path(__file__).resolve().with_name('execute_sampling_pair_local_score_v1.py')
s=p.read_text(encoding='utf-8').replace('sampling_model_AB_foldC_seed0_20261103_v1/paired_development_eval_v1','blue_pair_eval_v1').replace('0748d8e99c6589e47195a255abaf58f77751941e17c71e5e6ddb7c456ff059fa','a2a24869ca8b7300e1a804359c0a542bcba8473189eaa8f28d0c5aabb9e8bbe8').replace('下一步单独授权上述完整哈希，启动唯一一次本机CPU评分。','单独授权完整 SHA256')
exec(compile(s,str(p)+'[blue-pair-authorized-score]','exec'),{'__file__':str(p),'__name__':'__main__'})
