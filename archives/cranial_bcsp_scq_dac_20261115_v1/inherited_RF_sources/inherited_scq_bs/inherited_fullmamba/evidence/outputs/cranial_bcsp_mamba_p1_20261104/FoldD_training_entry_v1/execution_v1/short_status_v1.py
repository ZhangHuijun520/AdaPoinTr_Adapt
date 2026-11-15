import json,socket
from pathlib import Path
assert socket.gethostname()=='shu-common-25721452-notebook-v2iwsa-0'
p=Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p1/T0_foldD_seed0_train_20261106_v1')
d={n:(p/n).read_text() if (p/n).is_file() else None for n in ['exit_code.txt','completion.json','failure.json','startup_failure.json']}
d['metrics']=sum(1 for _ in (p/'metrics.jsonl').open()) if (p/'metrics.jsonl').exists() else 0
print(json.dumps(d))
