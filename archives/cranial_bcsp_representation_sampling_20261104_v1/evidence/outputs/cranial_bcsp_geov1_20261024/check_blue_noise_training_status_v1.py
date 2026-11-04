"""Reuse the fixed read-only observer; save a separate status-check receipt."""
from pathlib import Path
p=Path(__file__).resolve().with_name('observe_blue_noise_training_start_v1.py')
s=p.read_text(encoding='utf-8').replace('startup_observation','training_status_check_v1')
exec(compile(s,str(p)+'[status-check-v1]','exec'),{'__file__':str(p),'__name__':'__main__'})
