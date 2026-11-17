from pathlib import Path
import ast,base64,zlib,subprocess
V=Path(__file__).resolve().parent;S=V.parent
s=(S/'UTC_order_hotfix_v3/post_training_freeze_G0_C_v3.py').read_text(encoding='utf-8')
for a,b in [('post_training_freeze_v3','post_training_freeze_v1'),('bcsp_spcg_G0C_training_20261116_v3','bcsp_spcg_G0D_training_20261116_v1'),('SPCG_G0_C_training_execution_request_v3.json','SPCG_G0_D_training_execution_request_v1.json'),('871c5216815d5e479446108da979e8c77ce6ea5aec2578ac0573652e51a75d63','a877093becfd3e9763da36565c9401275e2f5ddd4f6d4f223fb4964ddf1d7fea'),('pending_transport_v3','pending_transport_v1'),('installation_mapping_v3.json','installation_mapping_v1.json'),('authorization_v3.json','authorization_v1.json'),('runtime_v3.json','runtime_v1.json'),('attempt_claim_v3.json','attempt_claim_v1.json'),("model['fold']=='C'","model['fold']=='D'"),("checks['G0C_identity']","checks['G0D_identity']"),("fold='C',arm='G0'","fold='D',arm='G0'"),('FORMAL_SPCG_G0_C_POST_TRAINING_FREEZE_PASS','FORMAL_SPCG_G0_D_POST_TRAINING_FREEZE_PASS'),("formal_freeze_result_v3.json').write_text","formal_freeze_result_v1.json').write_text")]:s=s.replace(a,b)
s=s.replace("code=PREFIX+body;","code=(PREFIX.split('def record(p):')[0] if label=='03_all3900_order_numeric' else PREFIX)+body;")
s=s.replace("close(m['loss'],sum(g['loss_components'].values()))","m['loss']==__import__('struct').unpack('f',__import__('struct').pack('f',sum(g['loss_components'].values())))[0]")
s=s.replace("detailed=[g for g in G", "assert all(g['frame']=='D_only_normalized' and set(g['loss_components'])=={'coarse_CD','dense_CD'} for g in G)\njson.dumps(G,allow_nan=False)\ndetailed=[g for g in G")
extra='''metadata=remote('04_D_metadata_C_prerequisites',"""qc=q['QC'];records={k:record(Path(qc[k]['path'])) for k in ['qualified_receipt','verification','fold_binding']};records.update({'manifest_'+k:record(Path(v['path'])) for k,v in qc['manifests'].items()})
fold=read(Path(qc['fold_binding']['path']))['folds']['D'];plan=read(o/'order_plan.json');M=[json.loads(l) for l in (o/'metrics.jsonl').read_text().splitlines()];proofs={k:dict(record=record(Path(v['path'])),value=read(Path(v['path']))) for k,v in q['C_matrix_freezes'].items()}
print(json.dumps(dict(records=records,proofs=proofs,D_selected_order=plan['case_ids']==fold['train_case_ids'],D_counts=len(fold['train_case_ids'])==315 and len(fold['train_sources'])==63 and len(fold['dev_sources'])==21,D_train_only=all(set(m['case_ids'])<=set(fold['train_case_ids']) and set(m['source_ids'])<=set(fold['train_sources']) for m in M),D_disjoint=not set(fold['train_sources'])&set(fold['dev_sources']))))
""")
for key,r in metadata['records'].items():
 target=q['QC']['manifests'][key.split('_',1)[1]] if key.startswith('manifest_') else q['QC'][key]
 checks['metadata_'+key]=r==dict(bytes=target['bytes'],sha256=target['sha256'])
for key in ['D_selected_order','D_counts','D_train_only','D_disjoint']:checks[key]=metadata[key]
for arm,item in metadata['proofs'].items():
 proof=item['value'];r=q['C_matrix_freezes'][arm]
 checks['C_matrix_freeze_'+arm]=item['record']==dict(bytes=r['bytes'],sha256=r['sha256']) and proof['status']=='FORMAL_SPCG_'+arm+'_C_POST_TRAINING_FREEZE_PASS' and all(proof['checks'].values())
base=metadata['proofs']['G0']['value']
checks['G0_shared_scratch_initialization']=base['initialization_raw_tensor_fingerprint']==q['expected_initial_state_sha256'] and all(base['initialization'][k]==state[k] for k in ['parameter_sha256','persistent_state_sha256','seed'])
checks['D_data_root']=q['data_root']==q['project']+'/data/bcsp_geov1_foldd_8192_seed0_v1'
'''
s=s.replace("result=dict(status=",extra+"result=dict(status=",1)
ast.parse(s);tree=ast.parse(s);pre=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PREFIX' for t in n.targets));lengths={}
for n in tree.body:
 if isinstance(n,ast.Assign) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='remote':
  label=ast.literal_eval(n.value.args[0]);prefix=pre.split('def record(p):')[0] if label=='03_all3900_order_numeric' else pre;code=prefix+ast.literal_eval(n.value.args[1]);compile(code,label,'exec');c="import base64,zlib;exec(zlib.decompress(base64.b64decode('"+base64.b64encode(zlib.compress(code.encode())).decode()+"')))";args=['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','60','--','/usr/bin/python3','-I','-S','-B','-c',c];lengths[label]=len(subprocess.list2cmdline(args).encode());assert lengths[label]<=2048
with (V/'post_training_freeze_G0_D_v1.py').open('x',encoding='utf-8') as f:f.write(s)
print(lengths)
