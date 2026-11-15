"""Adapt the retained CPU entry contracts to the new S-ref-first protocol."""
from pathlib import Path
import ast

R=Path(__file__).resolve().parent.parent
OLD=R/'outputs/cranial_bcsp_scq_foldC_training_preparation_20261113_v1'
O=R/'outputs/scq_rf_Sref_C_training_implementation_20261114_v1'
src=(OLD/'test_scq_training_entry_cpu_v3.py').read_text(encoding='utf-8')
for old,new in [('cpu_batch_v3','cpu_entry_batch_v1'),('bcsp_scq_training_entry_v1.py','bcsp_scq_rf_Sref_C_training_entry_v1.py'),
                ('bcsp_scq_training_bridge_v1.py','bcsp_scq_rf_training_bridge_v1.py'),('training_context_candidate_v1.json','context_v1.json'),
                ("ctx['request_candidate']","ctx['candidate']"),('SCQ_TRAINING_ENTRY_LOCAL_P3_PASS','RF_SREF_C_TRAINING_ENTRY_LOCAL_P3_PASS'),
                ('bcsp-scq-training-authorization-v1','bcsp-scq-rf-training-authorization-v1'),('bcsp-scq-training-runtime-v1','bcsp-scq-rf-training-runtime-v1'),
                ('outputs/cranial_bcsp_scq_cuda_preparation_20261113_v1','outputs/scq_rf_cuda_preparation_20261114_v2'),
                ('bcsp_scq_cuda_admission_v3.py','bcsp_scq_rf_cuda_admission_v2.py'),
                ("if not n.startswith('base_model.scq.')","if not n.startswith('base_model.rf.')"),
                ("for variant in ['B','S']:","for variant in ['S']:"),
                ('SCQ_TRAINING_ENTRY_ARTIFICIAL_CPU_PASS','RF_SREF_TRAINING_ENTRY_ARTIFICIAL_CPU_PASS'),
                ('B/S dispatch uses tiny artificial model','S-ref dispatch uses tiny artificial model')]:
    assert old in src,old;src=src.replace(old,new)
start=src.index("  sq=copy.deepcopy(q);sq['variant']='S'")
end=src.index("  allowed=e.payload_paths",start)
new="""  bad=copy.deepcopy(q);bad['arm']='RF-Static';reject('other arm forbidden in Sref first entry',lambda:authorize(bad))
  bad=copy.deepcopy(q);bad['paired_baseline']={'historical':'B'};reject('historical B dependency forbidden for Sref',lambda:authorize(bad))
  bad=copy.deepcopy(q);bad['variant']='B';reject('B model forbidden for Sref',lambda:authorize(bad))
  check('Sref first accepted without historical baseline',q['paired_baseline'] is None and admission['status']=='SCQ_RF_NATIVE_CUDA_ADMISSION_PASS')
"""
src=src[:start]+new+src[end:]
src=src.replace("allowed=e.payload_paths(q['data_root'],selected)","allowed=e.payload_paths(str(F/'train_root'),selected)")
src=src.replace("e.payload_paths(q['data_root'],badsel)","e.payload_paths(str(F/'train_root'),badsel)")
anchor="  # Original runtime optimizer grouping; never construct AdamW or run its lifecycle."
additional="""  current=authorize(q)
  check('current5forward admission includes full original SCQ state',common==ctx['expected_common'] if 'expected_common' in ctx else common==json.loads((R/'outputs/scq_rf_Sref_C_training_review_20261114_v1/training_contract_and_entry_review_v1.json').read_bytes())['expected_common_full_S_state_SHA256'])
  bad=copy.deepcopy(q);bad['run_id']='SCQ_S_foldC_seed0_train_OLD';reject('old stage run id rejected',lambda:authorize(bad))
  bad=copy.deepcopy(q);bad['stage']='CRANIAL_BCSP_SCQ';reject('old SCQ stage rejected',lambda:authorize(bad))
"""
assert anchor in src;src=src.replace(anchor,additional+anchor)
# Preserve the original source/hash and policy tests; just correct the actual new paths above.
src=src.replace("  print(json.dumps(dict(status='PASS',checks=len(checks))))", "  print(json.dumps(dict(status='PASS',checks=len(checks))))")
path=O/'test_scq_rf_Sref_C_entry_cpu_v1.py';compile(src,str(path),'exec')
with path.open('x',encoding='utf-8',newline='\n') as f:f.write(src)
print('SREF_C_CPU_TEST_PREPARED_NOT_RUN')
