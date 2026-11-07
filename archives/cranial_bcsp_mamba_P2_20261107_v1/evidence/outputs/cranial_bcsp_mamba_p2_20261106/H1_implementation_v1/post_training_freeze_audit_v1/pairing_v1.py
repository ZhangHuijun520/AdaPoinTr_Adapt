import hashlib,json,pathlib
R=pathlib.Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_h1_foldC_20261106_v1')
def read(p):return json.loads(pathlib.Path(p).read_bytes())
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
q=read(R/'M_H1_foldC_seed0_training_execution_request_v1.json');O=pathlib.Path(q['output'])
b=read(q['baseline_request']['path']);B=pathlib.Path(b['output']);audit=read(q['baseline_audit']['path'])
assert sha(q['baseline_request']['path'])==audit['request_sha256']=='48dedc867ce2a9c46bc1a6fdc7db3506b6f2405dbdf914de49cf561e2fe12b54'
assert sha(q['baseline_audit']['path'])=='bcbfb9a65742ab7c9da4a2d01c55b5f9a78bc77da66e38cf078f3074e0968815'
assert audit['checks_passed']==len(audit['checks']) and all(audit['checks'].values())
bindings={pathlib.Path(r['path']).name:r for r in audit['files'] if pathlib.Path(r['path']).parent==B}
names=['initialization.json','model_construction.json','optimizer_actual_defaults.json','optimizer_parameter_groups.json','run_identity.json','metrics.jsonl']
for n in names:assert sha(B/n)==bindings[n]['sha256'],n
initial=read(O/'initialization.json');assert initial==read(B/'initialization.json')==audit['initialization']['record']
construction=read(O/'model_construction.json');assert construction==read(B/'model_construction.json')
assert construction['factory']==read(q['initialization_reference']['path'])['factory']
assert construction['factory']['variant']=='M0' and construction['factory']['seed']==0 and not construction['factory']['artificial_fixture']
for n in ('optimizer_actual_defaults.json','optimizer_parameter_groups.json'):assert read(O/n)==read(B/n)
groups=read(O/'optimizer_parameter_groups.json');assert len(groups)==362
assert all(x['weight_decay'] in (0,.0005) for x in groups)
identity=read(O/'run_identity.json');old=read(B/'run_identity.json')
assert identity.pop('stage')=='CRANIAL_BCSP_MAMBA_P2_H1' and old.pop('stage')=='CRANIAL_BCSP_MAMBA_P1' and identity==old
current=[json.loads(s) for s in (O/'metrics.jsonl').read_text().splitlines()]
previous=[json.loads(s) for s in (B/'metrics.jsonl').read_text().splitlines()];assert len(current)==len(previous)==3900
keys=['step','epoch','batch','case_ids','source_ids','LR','BN_momentum','clip_max_norm','optimizer_step_committed']
assert all(all(x[k]==y[k] for k in keys) for x,y in zip(current,previous))
scope=read(q['preflight_scope']['path'])
for rec in scope['bindings']['isolated_model_project_sources']:
 if rec['relative_path'] in ('models/AdaPoinTr.py','extensions/chamfer_dist/__init__.py'):
  assert sha(pathlib.Path(q['model_root'])/rec['relative_path'])==rec['sha256']
print(json.dumps(dict(status='M0_BASELINE_INITIALIZATION_OPTIMIZER_FULL_ORDER_PAIR_PASS',initialization=initial,parameter_groups=len(groups),exact_factory_match=True,full3900_batch_and_schedule_match=True,H1_only_config_delta=True,final_weights_expected_to_differ=True,checkpoint_loaded=False,server_writes=0,limitation='Initial fingerprints and frozen construction metadata compared; initial tensors not rebuilt')),flush=True)
