"""Read-only startup confirmation for the single authorized graph attempt."""
from pathlib import Path
p=Path(__file__).resolve().with_name('observe_blue_noise_training_start_v1.py')
s=p.read_text(encoding='utf-8')
s=s.replace("O=B/'blue_noise_model_pair_foldC_seed0_20261104_v1/first_training_request_v2'","O=B/'blue_noise_model_pair_foldC_seed0_20261104_v1/first_training_request_v2/graph_request_v2'")
s=s.replace('Euclidean_training_execution_request_v1.json','candidate_training_execution_request_v1.json').replace('startup_observation','graph_start_observation')
s=s.replace("'completion':tail(P/'completion.json',5000)","'initialization':tail(P/'initialization.json',4000),'completion':tail(P/'completion.json',5000)")
exec(compile(s,str(p)+'[graph-start]','exec'),{'__file__':str(p),'__name__':'__main__'})
