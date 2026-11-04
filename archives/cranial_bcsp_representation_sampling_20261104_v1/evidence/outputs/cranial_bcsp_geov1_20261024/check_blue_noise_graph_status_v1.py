"""Separate read-only graph training status observation; no restart or writes."""
from pathlib import Path
p=Path(__file__).resolve().with_name('observe_blue_noise_graph_start_v1.py')
s=p.read_text(encoding='utf-8').replace("s=s.replace('Euclidean_training_execution_request_v1.json','candidate_training_execution_request_v1.json').replace('startup_observation','graph_start_observation')","s=s.replace('Euclidean_training_execution_request_v1.json','candidate_training_execution_request_v1.json').replace('startup_observation','graph_status_check_v1')")
assert 'graph_status_check_v1' in s
exec(compile(s,str(p)+'[status-check-v1]','exec'),{'__file__':str(p),'__name__':'__main__'})
