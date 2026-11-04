"""Render exact authorized blue-noise pair evaluation using unchanged frozen controller."""
import ast
from pathlib import Path
B=Path(__file__).resolve().parent
old='sampling_model_AB_foldC_seed0_20261103_v1/paired_development_eval_v1'
new='blue_pair_eval_v1'
p=B/'prepare_sampling_pair_authorized_execution_v1.py'
s=p.read_text(encoding='utf-8').replace(old,new).replace('76673ba94626253161dc70f0a33006d21c8094bced8148496c68c6c3490f0f4c','4fd0d2736e58530326c37d77fdbd5e76242339c36ea0a7905290a58d0b31ab43')
ast.parse(s)
exec(compile(s,str(p)+'[blue-pair-scope]','exec'),{'__file__':str(p),'__name__':'__main__'})
inv=(B/'invoke_sampling_pair_authorized_execution_v1.py').read_text(encoding='utf-8').replace(old,new)
ast.parse(inv)
with (B/'invoke_blue_pair_authorized_execution_v1.py').open('x',encoding='utf-8') as f:f.write(inv)
print('BLUE_PAIR_AUTHORIZED_RENDER_PASS_NO_SERVER_CALLS')
