import collections,hashlib,json,pathlib,math
R=pathlib.Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_h1_foldC_20261106_v1')
q=json.loads((R/'M_H1_foldC_seed0_training_execution_request_v1.json').read_bytes());O=pathlib.Path(q['output'])
def read(p):return json.loads(pathlib.Path(p).read_bytes())
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def bound(r):assert sha(r['path'])==r['sha256'];return r['path']
assert sha(O/'order_plan.json')==q['order_plan']['sha256']==sha(q['order_plan']['path'])
plan=read(O/'order_plan.json');assert len(plan['epochs'])==100 and len(set(plan['case_ids']))==315
fold=read(bound(q['QC']['fold_binding']))['folds']['C']
assert plan['case_ids']==fold['train_case_ids'] and len(set(fold['train_sources']))==63 and not set(fold['train_sources'])&set(fold['dev_sources'])
records=[json.loads(s) for s in pathlib.Path(bound(q['QC']['manifests']['8192'])).read_text().splitlines()]
source={r['case_id']:r['source_id'] for r in records if r['case_id'] in set(plan['case_ids'])}
assert len(source)==315 and set(collections.Counter(source.values()).values())=={5} and set(source.values())==set(fold['train_sources'])
rows=[json.loads(s) for s in (O/'metrics.jsonl').read_text().splitlines()];assert len(rows)==3900
cases,sources,drops=collections.Counter(),collections.Counter(),collections.Counter()
for e,epoch in enumerate(plan['epochs']):
 assert epoch['epoch']==e and len(epoch['batches'])==39 and len(epoch['dropped'])==3
 flat=sum(epoch['batches'],[])+epoch['dropped'];assert len(flat)==len(set(flat))==315 and set(flat)==set(plan['case_ids'])
 for b,batch in enumerate(epoch['batches']):
  r=rows[e*39+b];assert len(batch)==8 and r['case_ids']==batch and r['source_ids']==[source[c] for c in batch]
  assert r['LR']==[.0001*max(.9**(e/21),.02)]*2 and r['BN_momentum']==max(.9*.5**(e/21),.01)
  cases.update(batch);sources.update(r['source_ids'])
 drops.update(epoch['dropped'])
canonical=hashlib.sha256(json.dumps(plan,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
complete=read(O/'completion.json');initial=read(O/'initialization.json')
assert canonical==complete['order_sha256']==initial['order_sha256']
expected=dict(case=dict(cases),source=dict(sources),dropped_case=dict(drops),order_sha256=canonical)
assert read(O/'exposure.json')==expected and sum(cases.values())==sum(sources.values())==31200 and sum(drops.values())==300
base=read(bound(q['baseline_request']));old=pathlib.Path(base['output']);audit=read(bound(q['baseline_audit']))
bindings={pathlib.Path(r['path']).name:r for r in audit['files'] if pathlib.Path(r['path']).parent==old}
assert sha(old/'exposure.json')==bindings['exposure.json']['sha256'] and read(old/'exposure.json')==expected
print(json.dumps(dict(status='FULL_BATCH_ORDER_LR_BN_EXPOSURE_PAIR_PASS',cases=315,sources=63,updates=3900,traversals=100,exposures=31200,drops=300,order_sha256=canonical,raw_order_sha256=sha(O/'order_plan.json'),baseline_exposure_identical=True,server_writes=0)),flush=True)
