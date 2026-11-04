"""Local-only development-pair preparation: reuse samples/references, no resampling."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
import ast,hashlib,json,sys,time
from pathlib import Path
import numpy as np
B=Path(__file__).resolve().parent;O=B/'sampling_model_AB_foldC_seed0_20261103_v1';N=O/'paired_development_eval_v1'
OLD=B/'development_eval_v1';E=B/'spatial_stratified_expanded_20261103_v1';D=B/'real_data_qc_v1'
PROJECT='/home/jovyan/adapointr_work/PoinTr'
CODE=PROJECT+'/third_party/bcsp_sampling_ab_foldc_seed0_v1'
REMOTE=CODE+'/development_pair_v1';DATA=PROJECT+'/data/bcsp_sampling_ab_foldc_seed0_dev_v1'
ARMS=['V1','Morton_area_stratified8k']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ash(a):return hashlib.sha256(a.tobytes()).hexdigest()
def bind(p):return dict(path=str(Path(p).absolute()),bytes=Path(p).stat().st_size,sha256=sha(p))
def dump(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=True,indent=2,allow_nan=False)
def main():
 start=time.monotonic();N.mkdir()
 protocol=json.loads((O/'comparison_protocol_v1.json').read_bytes());ids=protocol['development_case_ids'];sources=protocol['development_sources']
 assert len(ids)==105 and len(set(ids))==105 and len(sources)==21 and not set(sources)&set(protocol['train_sources'])
 for arm in ARMS:(N/'data'/arm/'points').mkdir(parents=True)
 original={r['case_id']:r for r in map(json.loads,(D/'manifest_8192.jsonl').read_text(encoding='utf-8').splitlines())}
 expanded={r['raw_case_id']:r for r in json.loads((E/'all_case_results.json').read_bytes()) if r['dataset']=='SkullBreak'}
 refmanifest=OLD/'reference_bank_v2/reference_manifest_v1.json';refs=json.loads(refmanifest.read_bytes());assert not refs['model_predictions_used']
 reflut={r['case_id']:r for r in refs['cases'] if r['fold']=='C'};assert set(reflut)==set(ids)
 rows=[];pairs=[];refrows=[];source_records=[]
 for cid in ids:
  r=original[cid];assert r['source_id'] in sources
  p=D/r['point_path'];assert sha(p)==r['sha256']
  with np.load(p,allow_pickle=False) as z:base=z['partial'].copy();target=z['implant'].copy()
  assert base.shape==target.shape==(8192,3) and base.dtype==target.dtype==np.float32 and ash(target)==r['target_array_sha256']
  er=next(m for m in expanded[cid]['metrics'] if m['seed']==0 and m['method']=='Morton_area_stratified8k')
  ep=E/er['sample_path'];assert sha(ep)==er['sample_sha256']
  with np.load(ep,allow_pickle=False) as z:
   candidate=z['partial'].copy();assert np.array_equal(z['center'],np.array(r['normalization']['center'])) and float(z['scale'])==r['normalization']['scale']
   assert np.array_equal(candidate,((z['xyz']-z['center'])/z['scale']).astype(np.float32))
  digest=hashlib.sha256(('BCSP_SAMPLING_AB_V1|point-order|'+cid).encode('ascii')).digest()
  perm=np.random.Generator(np.random.PCG64(int.from_bytes(digest[:8],'big'))).permutation(8192);orderhash=ash(perm.astype('<i8'))
  assert np.array_equal(np.sort(perm),np.arange(8192))
  for arm,x in zip(ARMS,[base,candidate]):
   assert x.shape==(8192,3) and x.dtype==np.float32 and np.isfinite(x).all()
   partial=x[perm].copy();path=N/'data'/arm/'points'/(cid+'_8192.npz')
   with path.open('xb') as f:np.savez_compressed(f,partial=partial,implant=target)
   with np.load(path,allow_pickle=False) as z:assert set(z.files)=={'partial','implant'} and np.array_equal(z['partial'],partial) and np.array_equal(z['implant'],target) and np.array_equal(z['partial'][np.argsort(perm)],x)
   rec=bind(path);rec['path']=DATA+'/'+arm+'/points/'+path.name
   rows.append(dict(run='C_'+arm,arm=arm,fold='C',n_input=8192,case_id=cid,source_id=r['source_id'],input=rec,normalization=r['normalization'],target_array_sha256=r['target_array_sha256'],common_point_order_sha256=orderhash))
  ref=reflut[cid];assert all(ref[k]==r[k] for k in ['source_id','target_array_sha256','normalization'])
  assert bind(ref['path'])['sha256']==ref['sha256'] and Path(ref['path']).stat().st_size==ref['bytes']
  refrows.append(ref);source_records.extend([bind(p),bind(ep)])
  pairs.append(dict(case_id=cid,source_id=r['source_id'],target_array_sha256=r['target_array_sha256'],normalization=r['normalization'],common_point_order_sha256=orderhash))
  assert time.monotonic()-start<600
 runs=[]
 for arm,auditpath in zip(ARMS,[O/'post_V1_training_freeze_audit_v2/audit_report_v2.json',O/'post_Morton_training_freeze_audit_v1/audit_report_v1.json']):
  a=json.loads(auditpath.read_bytes());assert a['status']=='FORMAL_POST_TRAINING_FREEZE_AUDIT_PASS' and all(a['checks'].values())
  runs.append(dict(label='C_'+arm,arm=arm,fold='C',n_input=8192,checkpoint={k:a['checkpoint'][k] for k in ['path','bytes','sha256']},freeze_audit=bind(auditpath),train_sources=protocol['train_sources'],dev_sources=sources,dev_case_ids=ids))
 rows=sorted(rows,key=lambda r:(ARMS.index(r['arm']),ids.index(r['case_id'])))
 dump(N/'development_input_index_v1.json',dict(schema='bcsp-sampling-pair-development-index-v1',stage='BCSP_SAMPLING_AB_V1',data_root=DATA,runs=runs,inputs=rows))
 dump(N/'paired_development_data_receipt_v1.json',dict(status='PAIRED_105_CASES_210_INPUTS_VERIFIED',sources=21,cases=105,model_case_pairs=210,n_input=8192,n_target=8192,seed=0,point_geometry_resampled=False,GT_equal=True,common_input_permutation=True,model_predictions_used=False,raw_NRRD_read=False,pairs=pairs,source_records=source_records,seconds=time.monotonic()-start))
 dump(N/'reference_manifest_foldC_v1.json',dict(status='FROZEN_EXISTING_FOLD_C_105_REFERENCES',parent_manifest=bind(refmanifest),cases=refrows,model_predictions_used=False,new_references_built=False))
 source=(OLD/'bcsp_development_predict_v1.py').read_text(encoding='utf-8')
 begin=source.index('def validate_index(');end=source.index('def load_partial(',begin)
 validator='''DEVELOPMENT_DATA_ROOT=DATA_ROOT_LITERAL
def validate_index(index,folds):
 runs=index['runs'];rows=index['inputs'];arms=['V1','Morton_area_stratified8k'];fold=folds['folds']['C']
 require(index['schema']=='bcsp-sampling-pair-development-index-v1' and index['stage']=='BCSP_SAMPLING_AB_V1' and index['data_root']==DEVELOPMENT_DATA_ROOT,'paired index identity')
 require(len(runs)==2 and len(rows)==210 and [r['label'] for r in runs]==['C_'+a for a in arms],'two runs/210 forwards')
 require(len(fold['dev_case_ids'])==105 and len(set(fold['dev_case_ids']))==105 and len(fold['dev_sources'])==21 and set(fold['dev_sources']).isdisjoint(fold['train_sources']),'Fold C source separation')
 for run in runs:
  part=[r for r in rows if r['run']==run['label']]
  require(run['arm'] in arms and run['label']=='C_'+run['arm'] and run['fold']=='C' and run['n_input']==8192,'arm label/input')
  require(len(part)==105 and [r['case_id'] for r in part]==run['dev_case_ids']==fold['dev_case_ids'],'ordered105 dev cases')
  require(run['train_sources']==fold['train_sources'] and run['dev_sources']==fold['dev_sources'],'same source fold')
  require(len({r['source_id'] for r in part})==21,'21sources')
  for row in part:
   require(row['arm']==run['arm'] and row['fold']=='C' and row['n_input']==8192 and row['source_id'] in fold['dev_sources'] and row['source_id']=='train:'+row['case_id'].split('__')[1],'case/source/arm identity')
   expected=DEVELOPMENT_DATA_ROOT+'/'+run['arm']+'/points/'+row['case_id']+'_8192.npz'
   require(row['input']['path']==expected,'exact dev arm path');clean(expected)
 for a,b in zip(rows[:105],rows[105:]):
  require(a['arm']=='V1' and b['arm']=='Morton_area_stratified8k' and all(a[k]==b[k] for k in ['case_id','source_id','normalization','target_array_sha256','common_point_order_sha256']),'paired target/frame/permutation')
 return runs,rows

'''.replace('DATA_ROOT_LITERAL',repr(DATA))
 source=source[:begin]+validator+source[end:]
 source=source.replace('bcsp-four-model-development-prediction-v1','bcsp-sampling-pair-development-prediction-v1').replace('BCSP_INPUT_DENSITY_V1','BCSP_SAMPLING_AB_V1')
 source=source.replace('Four frozen B0 models,420','Two frozen B0 models,210').replace("out.parent==Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1')","out.parent==Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_sampling_ab_v1')")
 source=source.replace('forwards==420','forwards==210').replace('exact420','exact210').replace('forwards=420','forwards=210').replace('FOUR_MODEL_420_FORWARD_COMPLETE','SAMPLING_PAIR_210_FORWARD_COMPLETE')
 source=source.replace("rng_before=helper.tensor_sha(torch.get_rng_state());budget.sample", "rng_before=helper.tensor_sha(torch.get_rng_state());cuda_rng_before=helper.tensor_sha(torch.cuda.get_rng_state(0));py_rng_before=repr(random.getstate());np_rng_before=np.random.get_state();budget.sample")
 anchor="   after=helper.state_sha(model);require(before==after,'model parameters/BN state changed')"
 assert source.count(anchor)==1
 source=source.replace(anchor,anchor+"\n   rng_after=helper.tensor_sha(torch.get_rng_state());cuda_rng_after=helper.tensor_sha(torch.cuda.get_rng_state(0));np_rng_after=np.random.get_state()\n   require(rng_before==rng_after and cuda_rng_before==cuda_rng_after and py_rng_before==repr(random.getstate()) and np_rng_before[0]==np_rng_after[0] and np.array_equal(np_rng_before[1],np_rng_after[1]) and np_rng_before[2:]==np_rng_after[2:],'eval RNG state changed')")
 source=source.replace("CPU_rng_after=helper.tensor_sha(torch.get_rng_state()),mode=", "CPU_rng_after=rng_after,CUDA_rng_before=cuda_rng_before,CUDA_rng_after=cuda_rng_after,Python_numpy_RNG_unchanged=True,mode=")
 # Metadata provenance verified before installing the payload audit hook.
 anchor=" static=bound(q['static_config']);scope=bound(q['preflight_scope']);helper="
 assert source.count(anchor)==1
 source=source.replace(anchor," receipt=bound(q['paired_data_receipt']);require(receipt['status']=='PAIRED_105_CASES_210_INPUTS_VERIFIED' and receipt['GT_equal'] and receipt['common_input_permutation'],'paired dev receipt')\n"+anchor)
 ast.parse(source)
 with (N/'bcsp_sampling_pair_predict_v1.py').open('x',encoding='utf-8',newline='\n') as f:f.write(source)
 # Reuse exact fixed metric definitions; no new scoring/threshold selection.
 with (N/'bcsp_eval_metrics_v1.py').open('xb') as f:f.write((OLD/'bcsp_eval_metrics_v1.py').read_bytes())
 dump(N/'implementation_derivation_v1.json',dict(parent=bind(OLD/'bcsp_development_predict_v1.py'),candidate=bind(N/'bcsp_sampling_pair_predict_v1.py'),changes=['two Fold C sampling arms/210 calls and exact new dev paths','checkpoint task marker BCSP_SAMPLING_AB_V1','paired receipt validation','owned output parent','explicit Python/NumPy/CPU/CUDA RNG invariance assertions'],unchanged=['model/source/provider','forward implementation','state guard','numeric policy','resource limits','exclusive archive writer','one-way authorization'],metric_code_unchanged=bind(N/'bcsp_eval_metrics_v1.py')))
 print('LOCAL_105_PAIRED_INPUTS_AND_ENTRY_PREPARED_NO_MODEL_CALLS',flush=True)
if __name__=='__main__':
 sys.stdout.reconfigure(encoding='utf-8');main()
