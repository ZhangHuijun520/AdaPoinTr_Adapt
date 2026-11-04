"""Shorten local transport paths for Windows; scientific and server paths unchanged."""
import ast,json
from pathlib import Path
B=Path(__file__).resolve().parent
old=B/'blue_noise_model_pair_foldC_seed0_20261104_v1/first_training_request_v2/surface_graph_training_request_v1'
with (old/'local_preparation_failure_v1.json').open('x') as f:json.dump({'status':'NO_EXECUTION_REQUEST_CREATED','reason':'Windows MAX_PATH on long transport sidecar basename','server_writes':0,'training_calls':0},f,indent=2)
p=B/'prepare_blue_noise_graph_request_v1.py';s=p.read_text(encoding='utf-8')
s=s.replace('surface_graph_training_request_v1','graph_request_v2').replace('bcsp_blue_noise_ab_foldc_graph_control_v1','bcsp_graph_control_v1')
ast.parse(s)
exec(compile(s,str(p)+'[short-local-path]','exec'),{'__file__':str(p),'__name__':'__main__'})
