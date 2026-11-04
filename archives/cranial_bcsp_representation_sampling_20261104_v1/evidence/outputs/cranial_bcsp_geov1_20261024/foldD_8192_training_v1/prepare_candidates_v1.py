"""Local Fold D data/order and two-module adaptation; no GPU or server mutation."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,io,json,math,struct,zipfile
N=Path(__file__).resolve().parent;B=N.parent;I=N/'implementation_v1';I.mkdir(exist_ok=False)
P=B/'resource_rebind_implementation_v1/monitor_diagnostic_v3/research_priority_monitor_v4/new_container_training_v1'
CODE='/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1'
DATA='/home/jovyan/adapointr_work/PoinTr/data/bcsp_geov1_foldd_8192_seed0_v1'
CONTROL=CODE+'/control_train_foldD_8192_v1'
OUT='/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldD_in8192_out8192_seed0_train_v1'
def raw(p):return Path(p).read_bytes()
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(raw(p))
def dump(name,d):
 p=N/name
 with p.open('x',encoding='ascii',newline='\n') as f:json.dump(d,f,indent=2,ensure_ascii=True,allow_nan=False);f.write('\n')
 return p
def bind(p,server=None):
 r=dict(path=str(Path(p).absolute()),bytes=len(raw(p)),sha256=sha(raw(p)))
 if server:r['future_server_path']=server
 return r
def remote(p,target):return dict(path=target,bytes=len(raw(p)),sha256=sha(raw(p)))
q=load(P/'training_entry_request_v4.json');res=load(N/'resources_observation_v1.json');fresh=load(N/'freshness_observation_v1.json')
assert res['hostname']==q['identity']['hostname'] and res['uid']==1000
g=[x.strip() for x in res['gpu']['stdout'].strip().split(',')]
assert g[:4]==[q['identity']['gpu_uuid'],q['identity']['gpu_name'],q['identity']['driver_version'],'24564'] and int(g[4])<=256
assert res['compute_processes']['returncode']==0 and not res['compute_processes']['stdout'].strip() and res['disk']['free']>=4294967296
assert fresh['tmux_returncode']==1 and all(not p['exists'] and p['parent_writable'] for p in fresh['paths'])
folds=load(B/'consolidated_binding_v1/fold_binding.json');fold=folds['folds']['D'];ids=fold['train_case_ids'];sources=fold['train_sources']
assert len(ids)==len(set(ids))==315 and len(sources)==len(set(sources))==63 and len(fold['dev_sources'])==21
assert not set(sources)&set(fold['dev_sources']) and folds['confirmation_count_excluded']==20
assert sha(('\n'.join(ids)+'\n').encode())==fold['train_allowlist_sha256']=='682067ea877e8370e5c3d0ac7b2cdd7ae3b2b372a146829b42491899aa1c0aa1'
manifests={a:{r['case_id']:r for r in map(json.loads,raw(B/('real_data_qc_v1/manifest_'+a+'.jsonl')).decode().splitlines())} for a in ['8192','16384']}
for a in manifests:assert sha(raw(B/('real_data_qc_v1/manifest_'+a+'.jsonl')))==q['QC']['manifests'][a]['sha256']
# Reuse the exact standard-library NPY shape/hash inspection used for Fold C.
src=(B/'foldC_16384_training_v1/prepare_pair_v1.py').read_text();tree=ast.parse(src)
helpers='\n\n'.join(ast.get_source_segment(src,x) for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in ['npy','arrays'])
exec(compile(helpers,'bounded_existing_NPY_reader','exec'))
rows=[];total=0
for cid in ids:
 a=manifests['8192'][cid];b=manifests['16384'][cid]
 assert a['source_id'] in sources and a['source_id'] not in fold['dev_sources']
 assert all(a[k]==b[k] for k in ['source_id','target_array_sha256','normalization','normalization_source','raw'])
 pa,ta,sa=arrays(B/'real_data_qc_v1'/a['point_path'],a,8192)
 pb,tb,sb=arrays(B/'real_data_qc_v1'/b['point_path'],b,16384)
 assert ta==tb and pa==pb[:8192*3*4]
 rows.append(dict(case_id=cid,source_id=a['source_id'],point_path=a['point_path'],bytes=sa,sha256=a['sha256'],target_array_sha256=sha(ta),target_bytes_equal=True,input8192_is_prefix=True));total+=sa
assert len({r['case_id'] for r in rows})==315
pair=dump('paired315_data_verification_v1.json',dict(status='PASS_FOLD_D315_EXACT_PAIRING_AND_SOURCE_BOUNDARY',train_cases=315,train_sources=63,dev_sources=21,confirmation_sources_excluded=20,
 train_allowlist_sha256=fold['train_allowlist_sha256'],payload_bytes_8192=total,case_rows=rows,all_targets_byte_identical=True,all8192_inputs_are_16384_prefixes=True,
 shared_train_sources_with_C=len(set(sources)&set(folds['folds']['C']['train_sources'])),dev_payloads_read_for_FoldD=0,confirmation_payloads_read=0,data_regenerated=False))
c_order_path=B/'first_run_freeze_foldC_8192_v1/shared_order_foldC_seed0_v1.json'
cplan=load(c_order_path);assert sha(raw(c_order_path))=='6ab424177d5227bd34585a710eedca578acdd2eeb226bec10cdfc86ee89cec9d'
lookup={cid:i for i,cid in enumerate(cplan['case_ids'])};assert len(lookup)==315
plan=dict(schema='bcsp-shared-order-v1',case_ids=ids,epochs=[])
for e,row in enumerate(cplan['epochs']):
 target=dict(epoch=e,batches=[[ids[lookup[cid]] for cid in batch] for batch in row['batches']],dropped=[ids[lookup[cid]] for cid in row['dropped']])
 flat=[cid for batch in target['batches'] for cid in batch]+target['dropped']
 assert len(target['batches'])==39 and all(len(x)==8 for x in target['batches']) and len(target['dropped'])==3 and len(flat)==len(set(flat))==315 and set(flat)==set(ids)
 plan['epochs'].append(target)
assert len(plan['epochs'])==100
order=dump('shared_order_foldD_seed0_v1.json',plan)
order_evidence=dump('shared_order_derivation_v1.json',dict(status='FROZEN_FOLD_D_SHARED_POSITIONAL_PERMUTATIONS',source=bind(c_order_path),fold_binding=bind(B/'consolidated_binding_v1/fold_binding.json'),
 output=bind(order),algorithm='For each already frozen315-position permutation,substitute the Fold D fixed case at that position;no new RNG,shuffle or result-dependent selection',
 justification='Original make_order shuffles range315 with per-epoch generator;its indices do not depend on case strings;both folds have315 cases',
 use_for_both_D_input_arms=True,epochs=100,updates=3900,case_exposures=31200,dropped_exposures=300,
 chronological_case_order_changed_from_C=True,order_is_not_shared_case_ids_across_folds=True))
cp=I/'bcsp_training_contract_foldD_8192_v5.py'
old=raw(P/'bcsp_training_contract_01dt08_v3.py').decode()
text=old.replace("require(q['fold'] == 'C' and q['n_input'] == 8192, 'first rebound run only')","require(q['fold'] == 'D' and q['n_input'] == 8192, 'Fold D 8k arm only')")
assert text!=old
assert text.count("q['order_plan']['sha256'] == IMMUTABLE['order_plan']")==1
text=text.replace("q['order_plan']['sha256'] == IMMUTABLE['order_plan']","q['order_plan']['sha256'] == FOLD_D_ORDER_SHA")
text=text.replace('def authorize(request_record, authorization_record, runtime_record):',"# Current Fold D order is pinned separately; IMMUTABLE retains historical rebind evidence.\nFOLD_D_ORDER_SHA = '"+sha(raw(order))+"'\n\ndef authorize(request_record, authorization_record, runtime_record):")
with cp.open('x',encoding='utf-8',newline='\n') as f:f.write(text)
ep=I/'bcsp_training_entry_foldD_8192_v7.py'
text=raw(P/'bcsp_training_entry_research_v5.py').decode().replace('bcsp_training_contract_01dt08_v3.py',cp.name).replace('08a9af361ef0279cfccf27f9d094020501bfcc9859692ca64322d8dd4c7fd499',sha(raw(cp)))
with ep.open('x',encoding='utf-8',newline='\n') as f:f.write(text)
for p in [cp,ep]:compile(raw(p),str(p),'exec')
q['fold']='D';q['run_id']='bcsp_geov1_b0_foldD_in8192_out8192_seed0_train_v1';q['data_root']=DATA;q['output']=OUT;q['launch_attempt']=CONTROL+'/launch_attempt_v1.json'
q['order_plan']=remote(order,CODE+'/evidence/'+order.name)
q['implementation']['entry']=remote(ep,CODE+'/'+ep.name);q['implementation']['contract']=remote(cp,CODE+'/'+cp.name)
qualified=load(B/'first_run_freeze_foldC_8192_v1/qualified_data_qc_foldC_8192_v1.json');qualified['fold']='D';qualified['train_allowlist_sha256']=fold['train_allowlist_sha256']
qual=dump('qualified_data_qc_foldD_8192_v1.json',qualified);q['QC']['qualified_receipt']=remote(qual,CODE+'/evidence/'+qual.name)
candidate=dump('training_entry_request_candidate_v1.json',q)
# Adapt only the original controller's exact Fold C checks and data-byte total.
T=B/'resource_rebind_implementation_v1/first_training_request_foldC_8192_v1/local_byte_serialization_v2'
text=raw(T/'controller_template_v2.py').decode()
changes=[("q['fold'] == 'C'","q['fold'] == 'D'"),("qualified['fold'] == 'C'","qualified['fold'] == 'D'"),("['folds']['C']","['folds']['D']"),('payload_bytes == 49440750','payload_bytes == '+str(total))]
for a,b in changes:assert text.count(a)==1;text=text.replace(a,b)
controller=N/'controller_template_foldD_8192_v1.py'
with controller.open('x',encoding='utf-8',newline='\n') as f:f.write(text)
tree=ast.parse(text);pred={x.args[1].value:x.args[0] for x in ast.walk(tree) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='need' and len(x.args)==2 and isinstance(x.args[1],ast.Constant) and isinstance(x.args[1].value,str)}
values=dict(q=q,scope=dict(run_id=q['run_id']),qualified=qualified,r=manifests['8192'][ids[0]],counts={s:5 for s in sources},payload_bytes=total)
def evaluate(name,v):return eval(compile(ast.Expression(pred[name]),'<FoldDmetadata>','eval'),{},v)
for name in ['single frozen run','qualified QC exact paths','training data metadata','fixed315 payload bytes/sources']:assert evaluate(name,values)
v=copy.deepcopy(values);v['q']['fold']='C';assert not evaluate('single frozen run',v)
v=copy.deepcopy(values);v['q']['n_input']=16384;assert not evaluate('single frozen run',v)
v=copy.deepcopy(values);v['payload_bytes']-=1;assert not evaluate('fixed315 payload bytes/sources',v)
dump('candidate_static_review_v1.json',dict(status='PASS_MINIMAL_FOLD_D_ADAPTATION',contract_changes=['Dedicated D8192 arm gate','Separate exact Fold D order pin;historical rebind constants unchanged'],entry_changes='Sibling contract filename/SHA only',
 runtime_model_static_resources_data_sampling_unchanged=True,controller_changes=changes,controller_positive_predicates=4,controller_negative_predicates=3,
 order_derivation=bind(order_evidence),paired_data=bind(pair),candidate_request=bind(candidate),files=[bind(ep),bind(cp),bind(controller)],server_writes=0,model_calls=0))
print(json.dumps(dict(status='LOCAL_CANDIDATES_PREPARED_CPU_AUTHORIZE_TESTS_PENDING',cases=315,payload_bytes=total,order_SHA256=sha(raw(order)),server_writes=0)))
