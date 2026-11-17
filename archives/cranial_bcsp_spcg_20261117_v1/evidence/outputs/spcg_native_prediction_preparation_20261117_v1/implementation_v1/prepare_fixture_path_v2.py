from pathlib import Path
import ast,json,hashlib
V=Path(__file__).resolve().parent
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
freeze=json.loads((V/'CPU_failure_freeze_v1.json').read_text(encoding='utf-8'))
entry=V/'bcsp_spcg_sixmodel_native_predict_v1.py';assert rec(entry)['sha256']==freeze['entry_sha256']
old=(V/'test_spcg_native_CPU_v1.py').read_text(encoding='utf-8')
s=old.replace("O=V/'CPU_batch_v1'","O=V/'CPU_batch_v2'")
s=s.replace("  models={};D=torch.randn(1,8192,3)","  buildq=copy.deepcopy(q);buildq['mother_source']=rec(MOTHER);assert buildq['mother_source']['sha256']==q['mother_source']['sha256'] and buildq['mother_source']['bytes']==q['mother_source']['bytes']\n  models={};D=torch.randn(1,8192,3)")
assert s.count("dict(arm=arm),q,artificial_cpu=True")==1
s=s.replace("dict(arm=arm),q,artificial_cpu=True","dict(arm=arm),buildq,artificial_cpu=True")
ast.parse(s)
with (V/'test_spcg_native_CPU_v2.py').open('x',encoding='utf-8') as f:f.write(s)
q=json.loads((V/'draft_request_v1.json').read_text(encoding='utf-8'));aliases=json.loads((V/'local_metadata_map_v1.json').read_text(encoding='utf-8'))
paths=[entry,*[Path(aliases[r['path']]) for r in q['implementation'].values()],Path(aliases[q['mother_source']['path']])]
records=[rec(p) for p in paths]
(V/'fixture_path_static_review_v2.json').write_text(json.dumps(dict(status='STATIC_PASS_READY_SINGLE_CPU_V2',test=rec(V/'test_spcg_native_CPU_v2.py'),protected_sources=records,changes=['Local fixture buildq mother_source record only; same size/SHA.','New batch directory CPU_batch_v2; no reused failed batch.'],server_operations=0),ensure_ascii=False,indent=2),encoding='utf-8')
print('FIXTURE_PATH_STATIC_PASS_PRODUCTION_UNCHANGED')
