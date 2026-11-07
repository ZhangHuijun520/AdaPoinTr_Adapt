import hashlib,json,pathlib
R=pathlib.Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_H1_twofold_prediction_20261106_v1')
def read(p):return json.loads(pathlib.Path(p).read_bytes())
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
q=read(R/'H1_C_D_development_execution_request_v1.json');O=pathlib.Path(q['output']);done=read(O/'inference_complete.json');idx=read(q['input_index']['path'])
models=done['models'];assert len(models)==2 and [m['run'] for m in models]==['C_M_H1','D_M_H1']
summaries=[]
for m,run in zip(models,idx['runs']):
 assert m['forwards']==105 and m['mode']=='eval_inference_mode' and m['BNCal']==m['optimizer']==m['backward']==0
 assert m['state_before']==m['state_after'] and bool(m['state_before'])
 assert m['RNG_before']==m['RNG_after'] and set(m['RNG_before'])=={'CPU','CUDA','Python','numpy'}
 assert all(isinstance(v,str) and v for v in m['RNG_before'].values())
 c=m['construction'];assert c['variant']=='M0' and c['seed']==0 and c['replaced_global_branches']==6 and c['common_state_unchanged'] and not c['artificial_fixture']
 audit=read(q['training_audits'][run['fold']]['path']);assert audit['checks_passed']==len(audit['checks']) and all(audit['checks'].values())
 cp=pathlib.Path(run['checkpoint']['path']);record=next(x for x in audit['files'] if x['name']=='model_construction.json')
 p=cp.parent/'model_construction.json';assert sha(p)==record['sha256'] and read(p)['factory']==c
 initial=pathlib.Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p1/gpu_admission_20261104_v3/M0_construction.json')
 assert read(initial)['factory']==c
 summaries.append(dict(run=m['run'],forwards=105,state_identical=True,state_fingerprint=m['state_before'],RNG_identical=True,RNG_keys=sorted(m['RNG_before']),exact_training_factory_match=True))
print(json.dumps(dict(status='BOTH_MODELS_STATE_BN_RNG_FACTORY_PASS',models=summaries,server_writes=0,checkpoint_loaded=False,limitation='Frozen before/after digests and verified entry, not independent model replay or proof of continuous state equality')),flush=True)
