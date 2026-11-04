"""Freeze 210 development references and420 input identities; no prediction/model load."""
from pathlib import Path
import hashlib,json
N=Path(__file__).resolve().parent;B=N.parent
def raw(p):return Path(p).read_bytes()
def h(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(raw(p))
def bind(p):return dict(path=str(Path(p).absolute()),bytes=len(raw(p)),sha256=h(raw(p)))
def dump(name,obj):
 p=N/name
 with p.open('x',encoding='ascii') as f:json.dump(obj,f,indent=2,ensure_ascii=True)
 return p
P=B/'resource_rebind_implementation_v1/monitor_diagnostic_v3/research_priority_monitor_v4/new_container_training_v1'
folders={('C',8192):P,('C',16384):B/'foldC_16384_training_v1/authorize_gate_hotfix_v2',('D',8192):B/'foldD_8192_training_v1',('D',16384):B/'foldD_16384_training_v1'}
qfiles={('C',8192):'training_entry_request_v4.json',('C',16384):'training_entry_request_v2.json',('D',8192):'training_entry_request_v1.json',('D',16384):'training_entry_request_v1.json'}
training={key:load(folder/qfiles[key]) for key,folder in folders.items()}
foldpath=B/'consolidated_binding_v1/fold_binding.json';folds=load(foldpath)
manifest={str(n):{r['case_id']:r for r in map(json.loads,raw(B/('real_data_qc_v1/manifest_'+str(n)+'.jsonl')).decode().splitlines())} for n in [8192,16384]}
q0=training[('C',8192)]
for arm in manifest:assert h(raw(B/('real_data_qc_v1/manifest_'+arm+'.jsonl')))==q0['QC']['manifests'][arm]['sha256']
assert set(folds['folds']['C']['dev_sources']).isdisjoint(folds['folds']['D']['dev_sources']) and folds['confirmation_count_excluded']==20
runs=[];inputs=[];refs=[]
for fold in ['C','D']:
 spec=folds['folds'][fold];ids=spec['dev_case_ids'];sources=spec['dev_sources']
 assert len(ids)==len(set(ids))==105 and len(sources)==len(set(sources))==21 and not set(sources)&set(spec['train_sources'])
 for cid in ids:
  a=manifest['8192'][cid];b=manifest['16384'][cid]
  assert a['source_id'] in sources and all(a[k]==b[k] for k in ['source_id','target_array_sha256','normalization','raw'])
  refs.append(dict(case_id=cid,source_id=a['source_id'],fold=fold,normalization=a['normalization'],target_array_sha256=a['target_array_sha256'],
   raw={k:a['raw'][k] for k in ['defective','implant']},complete_raw_historical=a['raw']['complete'],
   original_case_QC=bind(B/'real_data_qc_v1/cases'/(cid+'.json')),
   point_files={str(n):bind(B/'real_data_qc_v1'/manifest[str(n)][cid]['point_path']) for n in [8192,16384]}))
 for arm in [8192,16384]:
  own=training[(fold,arm)];other=training[('D' if fold=='C' else 'C',arm)]
  report=load(folders[(fold,arm)]/'freeze_audit_v1/audit_report_v1.json')
  assert report['status']=='FORMAL_POST_TRAINING_FREEZE_AUDIT_PASS' and report['completion']['optimizer_updates']==3900
  checkpoint={k:report['checkpoint'][k] for k in ['path','bytes','sha256']}
  label=fold+'_'+str(arm)
  runs.append(dict(label=label,fold=fold,n_input=arm,training_run_id=own['run_id'],checkpoint=checkpoint,
   train_sources=spec['train_sources'],dev_sources=sources,dev_case_ids=ids,training_request=bind(folders[(fold,arm)]/qfiles[(fold,arm)]),freeze_audit=bind(folders[(fold,arm)]/'freeze_audit_v1/audit_report_v1.json')))
  for cid in ids:
   r=manifest[str(arm)][cid];local=B/'real_data_qc_v1'/r['point_path'];size=local.stat().st_size
   assert h(raw(local))==r['sha256'] and cid in folds['folds']['D' if fold=='C' else 'C']['train_case_ids']
   inputs.append(dict(run=label,fold=fold,n_input=arm,case_id=cid,source_id=r['source_id'],input=dict(path=other['data_root']+'/'+r['point_path'],bytes=size,sha256=r['sha256'])))
assert len(runs)==4 and len(inputs)==420 and len(refs)==210
index=dump('development_input_index_v1.json',dict(schema='bcsp-development-input-index-v1',runs=runs,inputs=inputs))
refindex=dump('reference_case_index_v1.json',dict(schema='bcsp-development-reference-index-v1',cases=refs))
root=next(p for p in N.parents if p.name=='mamba-ccf-c-1-high-resolution')
reader=root/'outputs/cranial_geometry_diagnostic_20261023/analyze_raw_pairs_v1.py'
protocol=root/'docs/cranial_bcsp_geov1_20261024/four_model_development_evaluation_protocol_zh_v1.md'
dump('reference_preparation_scope_v1.json',dict(schema='bcsp-development-reference-preparation-v1',status='FROZEN_BEFORE_MODEL_PREDICTIONS',
 case_index=bind(refindex),protocol=bind(protocol),raw_reader=bind(reader),original_QC=bind(B/'real_data_qc_verification_v1.json'),
 implementation=[bind(N/'bcsp_eval_metrics_v1.py'),bind(N/'build_reference_bank_v1.py')],
 raw_read_root='E:/dataset/SkullBreak/raw/train',output=str((N/'reference_bank_v1').absolute()),
 limits=dict(total_wall_seconds=3600,case_wall_seconds=120,RSS_bytes=8589934592,output_bytes=2147483648,threads=2),
 complete_C_decoded=False,complete_partition_proof='Inherited fixed all-source QC,with current D/G hashes rechecked;no fresh C decoding',model_predictions_available=False))
dump('preparation_index_receipt_v1.json',dict(status='FIXED_DEVELOPMENT_IDENTITIES',models=4,unique_sources=42,unique_cases=210,model_case_pairs=420,
 development_input_index=bind(index),reference_case_index=bind(refindex),point_data_reupload_required=False,model_calls=0))
print('fixed 4models/420inputs/210unique reference cases; no model calls')
