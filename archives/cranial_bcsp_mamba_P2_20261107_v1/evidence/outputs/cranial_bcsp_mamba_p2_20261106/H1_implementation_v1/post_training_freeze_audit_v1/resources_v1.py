import json,math,pathlib
R=pathlib.Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_h1_foldC_20261106_v1')
q=json.loads((R/'M_H1_foldC_seed0_training_execution_request_v1.json').read_bytes());O=pathlib.Path(q['output'])
rows=[json.loads(s) for s in (O/'resources.jsonl').read_text().splitlines()]
limits=json.loads(pathlib.Path(q['static_config']['path']).read_bytes())['resources']
assert len(rows)==3902
for i,r in enumerate(rows):
 phase='after_step' if i<3900 else 'before_final' if i==3900 else 'after_final'
 assert r['phase']==phase and r['committed_step']==min(i+1,3900) and r['limits']==limits
 assert r['resource_guard_passed'] is True and not r['failed_checks'] and all(r['checks'].values())
 assert r['RSS']<=limits['RSS_bytes'] and r['output_bytes']<=limits['output_bytes']
 assert r['peak_allocated']<=limits['torch_peak_bytes'] and r['peak_reserved']<=limits['torch_peak_bytes'] and r['device_MiB']<=limits['device_MiB']
 assert math.isfinite(r['elapsed_seconds']) and r['elapsed_seconds']<=limits['wall_seconds']
 assert r['PID_policy']=='DIAGNOSTIC_ONLY_NO_OWNERSHIP_GUARANTEE'
 assert i==0 or r['elapsed_seconds']>=rows[i-1]['elapsed_seconds']
complete=json.loads((O/'completion.json').read_bytes());assert complete['elapsed_seconds']<=limits['wall_seconds']
print(json.dumps(dict(status='ALL3902_RESOURCE_RECORDS_PASS',records=3902,max_RSS=max(r['RSS'] for r in rows),peak_allocated=max(r['peak_allocated'] for r in rows),peak_reserved=max(r['peak_reserved'] for r in rows),max_device_MiB=max(r['device_MiB'] for r in rows),PID_warning_records=sum(bool(r['PID_warning']) for r in rows),training_seconds=complete['elapsed_seconds'],limits=limits,server_writes=0,limitation='Sampled monitoring, not continuous isolation; free-disk checks supported by frozen runtime and exit0 rather than a saved numeric free-disk series')),flush=True)
