"""Use the exact existing CPU data reader, not a model, on all finalized840 NPZs."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
from pathlib import Path
B=Path(__file__).resolve().parent;O=B/'blue_noise_model_pair_foldC_seed0_20261104_v1'
import hashlib,importlib.util,json,sys,time
import numpy as np
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def arrsha(a):return hashlib.sha256(a.tobytes()).hexdigest()

def main():
    output=O/'actual_reader_verification_v1.json';assert not output.exists()
    start=time.monotonic();completion=json.loads((O/'data_preparation_completion.json').read_text())
    assert completion['status']=='PAIRED_FOLD_C_DATA_PREPARED_NOT_TRAINING_AUTHORIZED'
    scope=json.loads((B/'gpu_preflight_plotting_lazy_v3/artificial_gpu_zero_update_frozen_scope_v3.json').read_text())
    adapter_record=next(r for r in scope['bindings']['candidate'] if r['relative_target']=='tools/bcsp_adapter.py')
    path=Path(adapter_record['path']);assert sha(path)==adapter_record['sha256']
    spec=importlib.util.spec_from_file_location('unchanged_actual_bcsp_reader',path);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
    folds=json.loads((B/'consolidated_binding_v1/fold_binding.json').read_text())['folds']['C']
    counts={'train_point_files':0,'dev_input_files':0,'paired_train_targets':0};arms=['Euclidean_elimination','surface_graph']
    for split,manifest,allowed in [('train','train_manifest_8192.jsonl',folds['train_sources']),('development','dev_manifest_8192.jsonl',folds['dev_sources'])]:
        records={a:[json.loads(s) for s in (O/a/manifest).read_text().splitlines()] for a in arms}
        ids=[r['case_id'] for r in records[arms[0]]]
        assert ids==[r['case_id'] for r in records[arms[1]]]
        for i,cid in enumerate(ids):
            targets=[]
            for arm in arms:
                r=records[arm][i];assert r['comparison_split']==split
                partial,target=m.load_case(O/arm,r,set(allowed),8192,training=(split=='train'))
                assert partial.dtype==np.float32 and partial.shape==(8192,3) and np.isfinite(partial).all()
                if split=='train':
                    assert target.dtype==np.float32 and target.shape==(8192,3) and arrsha(target)==r['target_array_sha256']
                    targets.append(target);counts['train_point_files']+=1
                else:assert target is None;counts['dev_input_files']+=1
            if targets:assert np.array_equal(*targets);counts['paired_train_targets']+=1
    assert counts=={'train_point_files':630,'dev_input_files':210,'paired_train_targets':315}
    guard=m.UpdateGuard(m.Contract())
    for epoch in range(100):
        guard.begin_epoch(epoch,39)
        for _ in range(39):guard.before_step(8);guard.after_step()
        guard.end_epoch()
    state=guard.finish();assert state['optimizer_updates']==3900 and state['traversals']==100 and state['case_exposures']==31200
    assert sha(path)==adapter_record['sha256'] and 'torch' not in sys.modules
    result={'status':'PASS_UNCHANGED_ACTUAL_READER_AND_COUNTER','counts':counts,'adapter_sha256':adapter_record['sha256'],
      'counter_optimizer_updates':3900,'counter_exposures':31200,'counter_traversals':100,
      'development_reader_training_false_target_not_decoded':True,'models_GPU_calls':0,'seconds':time.monotonic()-start,
      'scope':'real NPZ data reader plus synthetic counter transitions; not model forward/backward or training'}
    with output.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
