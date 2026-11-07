"""Local static/P3 gap review and exact candidate assets; no model/data decoding."""
import ast,hashlib,json
from pathlib import Path
S=Path(__file__).resolve().parent;R=S.parents[2];P1=R/'outputs/cranial_bcsp_mamba_p1_20261104';Q=R/'outputs/cranial_bcsp_geov1_20261024/real_data_qc_v1'
def binding(p):
 p=Path(p);h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return dict(path=str(p),bytes=p.stat().st_size,sha256=h.hexdigest())
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def emit(name,value):
 with (S/name).open('x',encoding='utf-8') as f:json.dump(value,f,indent=2,allow_nan=False)
tests=read(S/'artificial_cpu_batch_v1/result_v1.json');assert tests['status']=='ARTIFICIAL_CPU_CONTRACT_PASS' and tests['tests']==20 and tests['failures']==tests['errors']==0
for name,h in tests['source_sha256'].items():assert binding(S/name)['sha256']==h
assert binding(S/'artificial_cpu_batch_v1/stdout_v1.txt')['sha256']==tests['stdout_sha256']
sources=[S/n for n in tests['source_sha256']]
for f in sources:ast.parse(f.read_text(encoding='utf-8'))
qc={r['case_id']:r for r in map(json.loads,(Q/'manifest_8192.jsonl').read_text(encoding='utf-8').splitlines())};assert len(qc)==420
all_inputs={};runs=[]
for fold,path in [('C',P1/'paired_development_evaluator_v2/transport_payload/paired_development_input_index_v1.json'),('D',P1/'FoldD_paired_development_preparation_v1/paired_development_input_index_v1.json')]:
 idx=read(path);assert len(idx['runs'])==2
 first=idx['runs'][0];train=sorted(c for c,r in qc.items() if r['source_id'] in first['train_sources']);dev=first['dev_case_ids'];assert len(train)==315 and len(dev)==105 and not set(train)&set(dev)
 assert len(first['train_sources'])==63 and len(first['dev_sources'])==21 and not set(first['train_sources'])&set(first['dev_sources'])
 for run in idx['runs']:
  assert run['fold']==fold and run['variant'] in ['T0','M0'] and run['train_sources']==first['train_sources'] and run['dev_case_ids']==dev
  p=Path('E:/ResearchBackups/AdaPoinTr/BCSP_MAMBA_P1/2026-11-06_P1_checkpoints_v1/weights')/(run['variant']+'_'+fold+'_epoch99_step3900.pth');b=binding(p)
  assert b['sha256']==run['checkpoint']['sha256'] and b['bytes']==run['checkpoint']['bytes']
  runs.append(dict(label=run['label'],fold=fold,variant=run['variant'],local_checkpoint=b,historical_server_checkpoint=run['checkpoint'],historical_server_path_not_current_presence_evidence=True,prediction_index=binding(path),training_audit_sha256=run['training_freeze_audit_sha256'],train_case_ids=train,dev_case_ids=dev))
 for role,ids in [('train',train),('development',dev)]:
  for cid in ids:
   row=qc[cid]
   if cid not in all_inputs:
    b=binding(Q/row['point_path']);assert b['sha256']==row['sha256'];all_inputs[cid]=dict(case_id=cid,source_id=row['source_id'],local_input=b,target_array_sha256=row['target_array_sha256'],normalization=row['normalization'],normalization_source=row['normalization_source'],roles=[])
   all_inputs[cid]['roles'].append(dict(fold=fold,role=role))
candidate=dict(status='LOCAL_CANDIDATE_ASSETS_HASH_VERIFIED_NOT_SERVER_READY',container_supplied_by_user='shu-common-25721452-notebook-1lvq9b-0',current_server_identity_verified=False,runs=runs,unique_point_files=list(all_inputs.values()),model_prefix_budget=1680,per_model=dict(train=315,development=105),backward=0,optimizer_steps=0,full_dense_forward=0,model_weights_loaded=False,data_arrays_decoded=False,original_manifest=binding(Q/'manifest_8192.jsonl'))
emit('local_candidate_assets_v1.json',candidate)
p3=dict(status='LOCAL_CORE_CPU_VALIDATED_EXECUTION_INTEGRATION_PENDING',tests=20,CPU_result=binding(S/'artificial_cpu_batch_v1/result_v1.json'),sources=[binding(p) for p in sources],static_AST_parse=True,checkpoint_local_hashes_verified=4,point_file_local_hashes_verified=420,real_model_loaded=False,real_forward_calls=0,server_operations=0,execution_request_created=False,review=dict(core_formula_and_train_only_standardization=True,mean_objective_lambda1_primal_dual_tested=True,actual_head_hook_exit_and_cleanup_tested=True,full_artificial_315_105_reader_tested=True,development_labels_not_fit=True,per_source_equal_summary=True),remaining_gaps=['New-container read-only identity/resources and exact source/provider/data presence check','Execution orchestration: bind existing model loader/resources/authorization and persistence to tested capture/readout core','Compare extracted development Q with frozen native summaries under inherited tolerance; no new permissive tolerance','Final CPU integration/P3 for the bounded runnable entry, then create separately authorized request'],limitations=['20 checks cover numerical/readout/capture core, not a runnable production GPU entry','Toy Torch modules and synthetic 315/105 rows do not establish Mamba/CUDA compatibility','Local checkpoint hashes do not establish server presence; no archive restoration performed'])
emit('local_core_P3_and_execution_gaps_v1.json',p3)
print(json.dumps(dict(status=p3['status'],tests=20,checkpoints=4,point_files=420,candidate=binding(S/'local_candidate_assets_v1.json'),P3=binding(S/'local_core_P3_and_execution_gaps_v1.json'))))
