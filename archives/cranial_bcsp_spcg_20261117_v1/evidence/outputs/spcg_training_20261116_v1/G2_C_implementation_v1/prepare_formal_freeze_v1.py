"""Prepare bounded G2/G1 read-only freeze audit; no server work in this generator."""
from pathlib import Path
import ast,base64,zlib,subprocess
V=Path(__file__).resolve().parent;S=V.parent
old=(S/'G1_C_implementation_v1/post_training_freeze_G1_C_v1.py').read_text(encoding='utf-8')
start=old[:old.index("pairing=remote('04_pair_G0_G1'")]
start=start.replace('G1','G2').replace('2d8ef3fff5db90653d0408ac6db72911e2c84b75aa61c9f03c8033aaf56ac0e4','f55806333bf52eef358aa718a77b3e7bbc58f2dd59e5de341d56f8ab9df73322')
pair='''pairing=remote('04_pair_G1_G2',"""g1=Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SPCG_G1_foldC_seed0_train_20261116_v1')
m1=[json.loads(l) for l in (g1/'metrics.jsonl').read_text().splitlines()];m2=[json.loads(l) for l in (o/'metrics.jsonl').read_text().splitlines()]
print(json.dumps(dict(order_identical=(g1/'order_plan.json').read_bytes()==(o/'order_plan.json').read_bytes(),exposure_identical=read(g1/'exposure.json')==read(o/'exposure.json'),initialization=read(g1/'initialization.json'),optimizer=read(g1/'optimizer_actual_defaults.json'),groups=read(g1/'optimizer_parameter_groups.json'),pair_rows=len(m1)==len(m2)==3900 and all(all(a[k]==b[k] for k in ['step','epoch','batch','case_ids','source_ids','LR','BN_momentum','clip_max_norm']) for a,b in zip(m1,m2)),parent_records={n:record(g1/n) for n in ['metrics.jsonl','initialization.json','order_plan.json','exposure.json','model_construction.json','optimizer_actual_defaults.json','optimizer_parameter_groups.json']},construction=read(g1/'model_construction.json'))))
""")
assets=remote('05_fixed_probe_head_and_parent_proofs',"""items={k:record(Path(q[k]['path'])) for k in ['probe_asset','head_initialization','mother_source','G0_C_freeze','G1_C_freeze']}
print(json.dumps(dict(records=items,free_bytes=os.statvfs(o).f_bavail*os.statvfs(o).f_frsize)))
""")
parent_dir=S/'G1_C_implementation_v1/post_training_freeze_v1'
parent=json.loads((parent_dir/'formal_freeze_result_v1.json').read_text(encoding='utf-8'))
parent_inv=json.loads((parent_dir/'01_inventory_checkpoint_result.json').read_text(encoding='utf-8'))
checks['G1_formal_freeze']=parent['status']=='FORMAL_SPCG_G1_C_POST_TRAINING_FREEZE_PASS' and all(parent['checks'].values())
checks['G1_evidence_unchanged']=all(v==parent_inv['files'][k] for k,v in pairing['parent_records'].items())
checks['paired_order_exposure_numeric']=all(pairing[k] for k in ['order_identical','exposure_identical','pair_rows'])
checks['same_full_initialization']=pairing['initialization']==state and q['expected_initial_state_sha256']==parent['initialization_raw_tensor_fingerprint']
checks['same_optimizer_defaults_and_groups']=pairing['optimizer']==opt and pairing['groups']==groups
checks['same_scratch_parent']=pairing['construction']['factory']['parent']==model['factory']['parent']
checks['G2_head_replaces_original']=model['factory']['change']['arm']=='G2' and model['factory']['change']['old_head_removed'] and model['factory']['change']['head_parameters']==1845763 and model['factory']['change']['additional_parameters']==8963
checks['one_coarse_expression_only']=model['factory']['change']['patch']['replaced_assignments']==1
for k,r in assets['records'].items():checks['asset_'+k]=r==dict(bytes=q[k]['bytes'],sha256=q[k]['sha256'])
pq=json.loads((S/'G1_C_implementation_v1/pending_transport_v1/payload/SPCG_G1_C_training_execution_request_v1.json').read_text(encoding='utf-8'))
for key in ['data_root','order_plan','static_config','identity','environment','probe_asset','head_initialization','mother_source','parent_G0_initial_state_sha256','counts','resources','science']:
 checks['paired_request_'+key]=q[key]==pq[key]
checks['G0_mother_same_as_G1']=q['parent_G0_initial_state_sha256']==pq['parent_G0_initial_state_sha256']
'''
end=old[old.index("result=dict(status="):].replace('G1','G2')
s=start+pair+end
ast.parse(s)
tree=ast.parse(s);prefix=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='PREFIX' for x in n.targets));sizes={}
for n in tree.body:
 if isinstance(n,ast.Assign) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='remote':
  label=ast.literal_eval(n.value.args[0]);pre=prefix.split('def record(p):')[0] if label=='03_all3900_order_numeric' else prefix;code=pre+ast.literal_eval(n.value.args[1]);compile(code,label,'exec');c="import base64,zlib;exec(zlib.decompress(base64.b64decode('"+base64.b64encode(zlib.compress(code.encode())).decode()+"')))";args=['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','60','--','/usr/bin/python3','-I','-S','-B','-c',c];sizes[label]=len(subprocess.list2cmdline(args).encode());assert sizes[label]<=2048
with (V/'post_training_freeze_G2_C_v1.py').open('x',encoding='utf-8') as f:f.write(s)
print(sizes)
