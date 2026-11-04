"""Local packaging fixture correction only; preserve failed v1 and production sources."""
import ast,hashlib,json
from pathlib import Path
B=Path(__file__).resolve().parent
p=B/'freeze_blue_noise_first_training_request_v1.py';s=p.read_text(encoding='utf-8')
failed=B/'blue_noise_model_pair_foldC_seed0_20261104_v1/first_training_request_v1'
record={'status':'LOCAL_PACKAGING_CHECK_FAILED_NO_REQUEST_CREATED','reason':'RAM lookup mapped JSON but not exact manifest files; production guard correctly rejected a Linux path on Windows','production_code_changes':0,'server_writes':0,'training_calls':0,'builder_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
with (failed/'local_preparation_failure_v1.json').open('x',encoding='utf-8') as f:json.dump(record,f,indent=2)
replacements=[("F=O/'first_training_request_v1'","F=O/'first_training_request_v2'"),('original=c.json_bound','original=c.json_bound;original_exact=c.exact'),
('    c.json_bound=resolve','    def exact_mapped(r):\n        p=mapping[r[\'path\']];assert p.stat().st_size==r[\'bytes\'] and sha(p)==r[\'sha256\'];return p\n    c.json_bound=resolve;c.exact=exact_mapped'),
('finally:c.json_bound=original','finally:c.json_bound=original;c.exact=original_exact')]
for old,new in replacements:
    assert s.count(old)==1,(old,s.count(old));s=s.replace(old,new)
ast.parse(s)
exec(compile(s,str(p)+'[local-fixture-v2]','exec'),{'__file__':str(p),'__name__':'__main__'})
