"""Finish local rendering after correcting only the line-count assertion (8 lines)."""
import ast,hashlib,json
from pathlib import Path
B=Path(__file__).resolve().parent;O=B/'blue_noise_model_pair_foldC_seed0_20261104_v1/first_training_request_v2';A=O/'authorized_execution_v1'
S='40a45089ed847261d9477993118b406048dadd09d15e492a402b455bddfdad74'
p=B/'prepare_blue_noise_authorized_execution_v1.py';s=p.read_text(encoding='utf-8')
s=s[s.index("p=A/'materialize_server_v1.py'"):]
exec(compile(s,str(p)+'[finish-static-render]','exec'),globals())
