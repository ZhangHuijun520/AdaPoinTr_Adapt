"""Read-only local download verification, no extraction or scoring."""
from pathlib import Path
p=Path(__file__).resolve().with_name('verify_sampling_pair_download_v1.py')
s=p.read_text(encoding='utf-8').replace('sampling_model_AB_foldC_seed0_20261103_v1/paired_development_eval_v1','blue_pair_eval_v1').replace('BCSP_SAMPLING_AB_V1/2026-11-03_paired_development_eval','BCSP_BLUE_NOISE_AB_V1/2026-11-04_paired_development_eval').replace('SAMPLING_PAIR_210_FORWARD_COMPLETE','BLUE_NOISE_PAIR_210_FORWARD_COMPLETE').replace('V1／Morton','欧氏／图距离')
exec(compile(s,str(p)+'[blue-pair-download]','exec'),{'__file__':str(p),'__name__':'__main__'})
