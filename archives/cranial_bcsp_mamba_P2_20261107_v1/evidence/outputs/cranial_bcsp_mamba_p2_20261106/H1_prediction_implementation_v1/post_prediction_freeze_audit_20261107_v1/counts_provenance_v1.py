import collections,hashlib,json,math,pathlib
R=pathlib.Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_H1_twofold_prediction_20261106_v1')
def read(p):return json.loads(pathlib.Path(p).read_bytes())
q=read(R/'H1_C_D_development_execution_request_v1.json');O=pathlib.Path(q['output']);idx=read(q['input_index']['path']);folds=read(q['fold_binding']['path'])['folds']
rows=[json.loads(x) for x in (O/'inference_manifest.jsonl').read_text().splitlines()]
journal=[json.loads(x) for x in (O/'forward_attempts.jsonl').read_text().splitlines()]
geometry=[json.loads(x) for x in (O/'geometry_summary.jsonl').read_text().splitlines()]
assert len(rows)==len(journal)==len(geometry)==len(idx['inputs'])==210
assert len({r['prediction']['name'] for r in rows})==210
checkpoints={r['label']:r['checkpoint']['sha256'] for r in idx['runs']}
for i,(r,j,g,x) in enumerate(zip(rows,journal,geometry,idx['inputs']),1):
 assert all(r[k]==x[k] for k in ['run','case_id','source_id','fold','variant','normalization']) and r['variant']=='M0'
 assert r['n_input']==r['n_output']==8192 and r['input_sha256']==x['input']['sha256'] and r['checkpoint_sha256']==checkpoints[r['run']]
 assert r['forward_index']==j['forward_index']==i and j['status']=='CLAIMED_BEFORE_FORWARD'
 assert j['run']==g['run']==r['run'] and j['case_id']==g['case_id']==r['case_id']
 assert r['prediction']['name']=='predictions/'+r['run']+'__'+r['case_id']+'.npz'
 p=O/r['prediction']['name'];assert p.stat().st_size==r['prediction']['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==r['prediction']['sha256']
 assert g['frame']=='native_D_only_normalized_no_GT' and math.isfinite(r['operational_seconds'])
 for part in ['coarse','dense']:
  a=g[part];assert all(math.isfinite(v) for k in ['centroid','bbox_min','bbox_max','covariance_eigenvalues'] for v in a[k]) and math.isfinite(a['radius_gyration'])
for f in ['C','D']:
 part=[r for r in rows if r['fold']==f];spec=folds[f]
 assert len(part)==105 and [r['case_id'] for r in part]==spec['dev_case_ids']
 counts=collections.Counter(r['source_id'] for r in part);assert len(counts)==21 and set(counts.values())=={5} and set(counts)==set(spec['dev_sources'])
 assert not set(spec['train_sources'])&set(spec['dev_sources'])
done=read(O/'inference_complete.json');assert done['status']=='P2_H1_TWOFOLD_210_FORWARD_COMPLETE' and done['forwards']==210
assert done['training_updates']==done['BNCal']==done['loss']==done['backward']==0
assert done['request_sha256']=='90df035abba6cb6651f323ce65f5477f2a9bd0b3a7a505a5ebcc376b7436c147'
print(json.dumps(dict(status='EXACT210_MANIFEST_JOURNAL_GEOMETRY_PROVENANCE_PASS',models=2,per_fold=105,total=210,unique_sources=42,loss=0,backward=0,optimizer_steps=0,BNCal=0,server_writes=0)),flush=True)
