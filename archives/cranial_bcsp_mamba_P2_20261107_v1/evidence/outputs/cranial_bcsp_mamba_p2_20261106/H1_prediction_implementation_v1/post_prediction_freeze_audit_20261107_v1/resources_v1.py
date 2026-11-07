import json,math,pathlib
R=pathlib.Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_H1_twofold_prediction_20261106_v1')
q=json.loads((R/'H1_C_D_development_execution_request_v1.json').read_bytes());O=pathlib.Path(q['output']);L=q['limits']
rows=[json.loads(x) for x in (O/'resources.jsonl').read_text().splitlines()]
expected=[('model_start:C_M_H1',0)]+sum(([('before_forward',i-1),('after_forward',i)] for i in range(1,106)),[])+[('model_start:D_M_H1',105)]+sum(([('before_forward',i-1),('after_forward',i)] for i in range(106,211)),[])+[('all_complete',210)]
assert len(rows)==len(expected)==423
for r,w in zip(rows,expected):
 assert (r['phase'],r['forwards'])==w and not r['failed_checks'] and all(r['checks'].values())
 v=r['values'];assert all(math.isfinite(x) and x>=0 for x in v.values())
 assert v['RSS_bytes']<=L['RSS_bytes'] and v['output_bytes']<=L['output_bytes'] and v['device_MiB']<=L['device_MiB']
 assert v['peak_allocated']<=L['torch_peak_bytes'] and v['peak_reserved']<=L['torch_peak_bytes'] and v['elapsed_seconds']<=L['wall_seconds'] and v['free_disk_bytes']>=L['minimum_free_disk_bytes']
 assert r['PID_policy']=='DIAGNOSTIC_ONLY_NO_OWNERSHIP_GUARANTEE'
peaks={k:max(r['values'][k] for r in rows) for k in ['RSS_bytes','output_bytes','device_MiB','peak_allocated','peak_reserved','elapsed_seconds']}
print(json.dumps(dict(status='ALL423_RESOURCE_RECORDS_PASS',records=423,peaks=peaks,minimum_free_disk_bytes=min(r['values']['free_disk_bytes'] for r in rows),server_writes=0,limitation='Sampled resource monitoring and diagnostic PID policy, not continuous hard isolation')),flush=True)
