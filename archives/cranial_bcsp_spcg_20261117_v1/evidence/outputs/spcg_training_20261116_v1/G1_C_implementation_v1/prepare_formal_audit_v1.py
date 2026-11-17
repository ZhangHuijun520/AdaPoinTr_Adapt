from pathlib import Path
import ast
V=Path(__file__).resolve().parent
s=(V.parent/'UTC_order_hotfix_v3/post_training_freeze_G0_C_v3.py').read_text(encoding='utf-8')
s=s.replace("V=Path(__file__).resolve().parent;S=V.parent;W=S.parents[1];O=V/'post_training_freeze_v3'", "V=Path(__file__).resolve().parent;S=V.parent;W=S.parents[1];O=V/'post_training_freeze_v1'")
for a,b in [('bcsp_spcg_G0C_training_20261116_v3','bcsp_spcg_G1C_training_20261116_v1'),('SPCG_G0_C_training_execution_request_v3.json','SPCG_G1_C_training_execution_request_v1.json'),('871c5216815d5e479446108da979e8c77ce6ea5aec2578ac0573652e51a75d63','2d8ef3fff5db90653d0408ac6db72911e2c84b75aa61c9f03c8033aaf56ac0e4'),('pending_transport_v3','pending_transport_v1'),('installation_mapping_v3.json','installation_mapping_v1.json'),('authorization_v3.json','authorization_v1.json'),('runtime_v3.json','runtime_v1.json'),('attempt_claim_v3.json','attempt_claim_v1.json')]:s=s.replace(a,b)
s=s.replace("close(m['loss'],sum(g['loss_components'].values()))", "m['loss']==__import__('struct').unpack('f',__import__('struct').pack('f',sum(g['loss_components'].values())))[0]")
s=s.replace('code=PREFIX+body;', "code=(PREFIX.split('def record(p):')[0] if label=='03_all3900_order_numeric' else PREFIX)+body;")
s=s.replace("detailed=[g for g in G", "assert all(g['frame']=='D_only_normalized' and set(g['loss_components'])=={'coarse_CD','dense_CD'} for g in G)\njson.dumps(G,allow_nan=False)\ndetailed=[g for g in G")
s=s.replace("model['factory']==native['result']['models']['G0']['construction']['parent']", "model['factory']['parent']==native['result']['models']['G0']['construction']['parent']")
s=s.replace("native['result']['models']['G0']['initial_state_sha256']", "native['result']['models']['G1']['initial_state_sha256']")
s=s.replace("model['arm']=='G0'", "model['arm']=='G1'").replace("checks['G0C_identity']", "checks['G1C_identity']")
s=s.replace("and not any(g['name'].startswith(('base_model.spcg_head.','base_model.scq.','base_model.rf.')) for g in groups)", "and not any(g['name'].startswith(('base_model.scq.','base_model.rf.')) for g in groups)")
pos=s.index("result=dict(status=")
pair_code='''pairing=remote('04_pair_G0_G1',"""g0=Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SPCG_G0_foldC_seed0_train_20261116_v3')
pair=read(Path(q['G0_C_freeze']['path'])) if 'G0_C_freeze' in q else None
m0=[json.loads(l) for l in (g0/'metrics.jsonl').read_text().splitlines()];m1=[json.loads(l) for l in (o/'metrics.jsonl').read_text().splitlines()]
print(json.dumps(dict(order_identical=(g0/'order_plan.json').read_bytes()==(o/'order_plan.json').read_bytes(),exposure_identical=read(g0/'exposure.json')==read(o/'exposure.json'),initialization_G0=read(g0/'initialization.json'),pair_rows=len(m0)==len(m1)==3900 and all(all(a[k]==b[k] for k in ['step','epoch','batch','case_ids','source_ids','LR','BN_momentum','clip_max_norm']) for a,b in zip(m0,m1)),G0_log_records={n:record(g0/n) for n in ['metrics.jsonl','initialization.json','order_plan.json','exposure.json']},construction=read(o/'model_construction.json'))))
""")
parent_dir=S/'UTC_order_hotfix_v3/post_training_freeze_v3'
parent=json.loads((parent_dir/'formal_freeze_result_v3.json').read_text(encoding='utf-8'))
parent_inv=json.loads((parent_dir/'01_inventory_checkpoint_result.json').read_text(encoding='utf-8'))
checks['G0_formal_freeze']=parent['status']=='FORMAL_SPCG_G0_C_POST_TRAINING_FREEZE_PASS' and all(parent['checks'].values())
checks['G0_evidence_unchanged']=all(v==parent_inv['files'][k] for k,v in pairing['G0_log_records'].items())
checks['paired_order_exposure_numeric']=all(pairing[k] for k in ['order_identical','exposure_identical','pair_rows'])
checks['shared_scratch_mother']=q['parent_G0_initial_state_sha256']==parent['initialization_raw_tensor_fingerprint']
checks['same_training_seed']=pairing['initialization_G0']['seed']==state['seed']==0
for key in ['data_root','order_plan','static_config','identity','environment']:
 pq=json.loads((S/'UTC_order_hotfix_v3/pending_transport_v3/payload/SPCG_G0_C_training_execution_request_v3.json').read_text(encoding='utf-8'))
 checks['paired_request_'+key]=q[key]==pq[key]
'''
s=s[:pos]+pair_code+s[pos:]
s=s.replace('FORMAL_SPCG_G0_C_POST_TRAINING_FREEZE_PASS','FORMAL_SPCG_G1_C_POST_TRAINING_FREEZE_PASS',1 if False else 0) if False else s
# Only change final result identity, retaining the parent's required status.
s=s.replace("result=dict(status='FORMAL_SPCG_G0_C_POST_TRAINING_FREEZE_PASS'", "result=dict(status='FORMAL_SPCG_G1_C_POST_TRAINING_FREEZE_PASS'")
s=s.replace("fold='C',arm='G0'", "fold='C',arm='G1'")
s=s.replace("formal_freeze_result_v3.json').write_text", "formal_freeze_result_v1.json').write_text")
ast.parse(s)
(V/'post_training_freeze_G1_C_v1.py').write_text(s,encoding='utf-8')
print('STATIC_PASS: read-only audit generated; no remote invocation')
