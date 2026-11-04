"""Prepare one bounded read-only audit; never imports model code."""
from pathlib import Path
import hashlib,json
N=Path(__file__).resolve().parent
P=N.parent.parent/'resource_rebind_implementation_v1/monitor_diagnostic_v3/research_priority_monitor_v4/new_container_training_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
parent_path=P/'freeze_audit_v1/audit_report_v1.json'
assert sha(parent_path)=='8c7eabba742d5eda2853da437c9df55380f9d0802a8da165d9351dfc898307bf'
parent=json.loads(parent_path.read_bytes())
scope=json.loads((N/'training_execution_request_v2.json').read_bytes())
pair_path=Path(scope['parent_evidence']['paired_data']['path'])
assert sha(pair_path)==scope['parent_evidence']['paired_data']['sha256']
pair=json.loads(pair_path.read_bytes())
assert pair['status']=='PASS_315_EXACT_TARGET_PREFIX_AND_PROVENANCE_PAIRS' and pair['all_targets_byte_identical'] and pair['all8192_inputs_are_16384_prefixes']
records=[]
for row in parent['output_manifest']:
 if row['path'].rsplit('/',1)[1] in ['initialization.json','metrics.jsonl','exposure.json','order_plan.json','completion.json','optimizer_actual_defaults.json']:
  records.append({k:row[k] for k in ['path','bytes','sha256']})
events=json.loads((P/'authorized_execution_v1/training_server_events_v1.json').read_bytes())
parent_q=next(r for e in events if e.get('status')=='TRAIN_MATERIALIZED_AND_ATTEMPT_CLAIMED' for r in e['files'] if r['path'].endswith('/training_execution_request_v1.json'))
prefix='PARENT_RECORDS='+repr(records)+'\nPARENT_REQUEST='+repr(parent_q)+'\n'
prefix+='LOCAL_PAIRED_PAYLOAD_EVIDENCE='+repr(dict(path=str(pair_path),sha256=sha(pair_path),paired_cases=315,all_targets_byte_identical=True,all8192_inputs_are_16384_prefixes=True))+'\n'
source=(P/'post_training_audit_v1.py').read_text()
source=source.replace("CONTROL=CODE/'control_train_v3'","CONTROL=CODE/'control_train_foldC_16384_v2'")
source=source.replace('b0_foldC_in8192_out8192_seed0_train_v3','b0_foldC_in16384_out8192_seed0_train_v2')
source=source.replace('16655f4494fe2458619129958a370d240866a15b339ec2d40b595d827b675f0a','7221de1a48d700f3e2b90e3904689c9e63239832203356785e8cd0f2278de2fd')
source=source.replace('training_execution_scope_v3.json','training_execution_scope_v1.json')
source=source.replace("q['QC']['manifests']['8192']","q['QC']['manifests']['16384']")
extra='''
 import ast
 parent_files={}
 for record in PARENT_RECORDS:
  parent_files[Path(record['path']).name]=read(record['path'],record)
 p8=js(PARENT_REQUEST['path'],PARENT_REQUEST)
 def parent_json(name):return json.loads(parent_files[name][1])
 pair_checks={}
 def paircheck(name,ok):
  pair_checks[name]=bool(ok);check('paired_'+name,ok)
 paircheck('arms16k_vs8k_target8192',q['n_input']==16384 and p8['n_input']==8192 and static['model']['num_points']==8192)
 paircheck('same_static_order_identity_model_runtime_backend',all(q[k]==p8[k] for k in ['static_config','order_plan','identity','model_root','preflight_scope','preflight_request_sha256']) and all(q['implementation'][k]==p8['implementation'][k] for k in ['runtime','preflight_helper']))
 paircheck('same_source_fold_and_manifest_bindings',q['fold']==p8['fold']=='C' and all(q['QC'][k]==p8['QC'][k] for k in ['verification','manifests','fold_binding']))
 initial=js(OUT/'initialization.json')
 paircheck('same_initial_parameters_persistent_state_seed_order',initial==parent_json('initialization.json')==scope['paired_8k_parent']['expected_same_initialization'])
 paircheck('same_exact_order_and_exposure_counters',plan==parent_json('order_plan.json') and exposure==parent_json('exposure.json'))
 m8=list(map(json.loads,parent_files['metrics.jsonl'][1].decode().splitlines()))
 paircheck('same_actual3900_batches_case_source_order',len(m8)==len(metrics)==3900 and all(all(a[k]==b[k] for k in ['step','epoch','batch','case_ids','source_ids']) for a,b in zip(m8,metrics)))
 paircheck('same_recorded_optimizer_defaults',js(OUT/'optimizer_actual_defaults.json')==parent_json('optimizer_actual_defaults.json'))
 paircheck('same_full_counts_and_no_BNCal_eval_resume',complete['counts']==parent_json('completion.json')['counts'] and all(parent_json('completion.json')[k] is False for k in ['bncal_executed','evaluation_executed','resume']))
 r8=p8['QC']['manifests']['8192'];other={x['case_id']:x for x in map(json.loads,read(r8['path'],r8)[1].decode().splitlines())}
 paircheck('same315_target_provenance_normalization',all(all(manifest[c][k]==other[c][k] for k in ['source_id','target_array_sha256','normalization','normalization_source','raw']) and manifest[c]['n_input']==16384 and other[c]['n_input']==8192 and manifest[c]['n_target']==other[c]['n_target']==8192 for c in fold['train_case_ids']))
 old_entry=read(p8['implementation']['entry']['path'],p8['implementation']['entry'])[1].decode()
 new_entry=read(q['implementation']['entry']['path'],q['implementation']['entry'])[1].decode()
 old_entry=old_entry.replace(Path(p8['implementation']['contract']['path']).name,Path(q['implementation']['contract']['path']).name).replace(p8['implementation']['contract']['sha256'],q['implementation']['contract']['sha256'])
 paircheck('entry_AST_same_except_contract_origin_pin',ast.dump(ast.parse(old_entry))==ast.dump(ast.parse(new_entry)))
 old_contract=read(p8['implementation']['contract']['path'],p8['implementation']['contract'])[1].decode()
 new_contract=read(q['implementation']['contract']['path'],q['implementation']['contract'])[1].decode()
 old_contract=old_contract.replace("require(q['fold'] == 'C' and q['n_input'] == 8192, 'first rebound run only')","require(q['fold'] == 'C' and q['n_input'] == 16384, 'Fold C 16k arm only')")
 paircheck('contract_AST_same_except_dedicated_arm_gate',ast.dump(ast.parse(old_contract))==ast.dump(ast.parse(new_contract)))
'''
marker=" check('result_tree_stable_atime_excluded',tree()==before)"
assert source.count(marker)==1;source=source.replace(marker,extra+'\n'+marker)
source=source.replace("exact_source_runtime_binding_verified=True,", "paired_consistency=pair_checks,paired_payload_evidence=LOCAL_PAIRED_PAYLOAD_EVIDENCE,exact_source_runtime_binding_verified=True,")
source=prefix+source
compile(source,'fixed16k_pair_audit','exec')
with (N/'post_training_audit_v1.py').open('x',encoding='utf-8',newline='\n') as f:f.write(source)
invoke=(P/'invoke_post_training_audit_v1.py').read_text()
with (N/'invoke_post_training_audit_v1.py').open('x',encoding='utf-8',newline='\n') as f:f.write(invoke)
print('fixed16k/pair readonly audit prepared; original budgets retained:32 entries,512MiB,90seconds;no weight load or point payload read')
