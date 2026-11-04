"""Prepare final paired arm only; no model calls, server mutation or new sampling."""
from pathlib import Path
import ast,copy,hashlib,io,json,math,struct,zipfile
N=Path(__file__).resolve().parent;B=N.parent;D=B/'foldD_8192_training_v1';I=N/'implementation_v1';I.mkdir(exist_ok=False)
def raw(p):return Path(p).read_bytes()
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(raw(p))
def dump(name,d):
 p=N/name
 with p.open('x',encoding='ascii',newline='\n') as f:json.dump(d,f,indent=2,ensure_ascii=True,allow_nan=False);f.write('\n')
 return p
def bind(p):return dict(path=str(Path(p).absolute()),bytes=len(raw(p)),sha256=sha(raw(p)))
def remote(p,target):return dict(path=target,bytes=len(raw(p)),sha256=sha(raw(p)))
audit=D/'freeze_audit_v1/audit_report_v1.json'
assert sha(raw(audit))=='74dff3d3134d490e73db6bf5ed24ab9a7c8e4724f81c867a4906fd2431ca3800'
assert load(audit)['status']=='FORMAL_POST_TRAINING_FREEZE_AUDIT_PASS'
q=load(D/'training_entry_request_v1.json');baseq=copy.deepcopy(q)
resources=load(N/'resources_observation_v1.json');fresh=load(N/'freshness_observation_v1.json');assets=load(N/'assets_observation_v1.json')
g=[x.strip() for x in resources['gpu']['stdout'].strip().split(',')]
assert resources['hostname']==q['identity']['hostname'] and resources['uid']==1000
assert g[:4]==[q['identity']['gpu_uuid'],q['identity']['gpu_name'],q['identity']['driver_version'],'24564'] and int(g[4])<=256
assert not resources['compute_processes']['stdout'].strip() and resources['disk']['free']>=4294967296
assert fresh['tmux_returncode']==1 and all(not x['exists'] and x['parent_writable'] for x in fresh['paths'])
fold=load(B/'consolidated_binding_v1/fold_binding.json')['folds']['D'];ids=fold['train_case_ids']
assert len(ids)==315 and len(fold['train_sources'])==63 and not set(fold['train_sources'])&set(fold['dev_sources'])
assert sha(('\n'.join(ids)+'\n').encode())=='682067ea877e8370e5c3d0ac7b2cdd7ae3b2b372a146829b42491899aa1c0aa1'
records={a:{r['case_id']:r for r in map(json.loads,raw(B/('real_data_qc_v1/manifest_'+a+'.jsonl')).decode().splitlines())} for a in ['8192','16384']}
for a in records:assert sha(raw(B/('real_data_qc_v1/manifest_'+a+'.jsonl')))==q['QC']['manifests'][a]['sha256']
source=(B/'foldC_16384_training_v1/prepare_pair_v1.py').read_text();tree=ast.parse(source)
helpers='\n\n'.join(ast.get_source_segment(source,x) for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in ['npy','arrays'])
exec(compile(helpers,'existing_bounded_NPY_reader','exec'))
rows=[];total=0
for cid in ids:
 a=records['8192'][cid];b=records['16384'][cid]
 assert b['source_id'] in fold['train_sources'] and b['source_id'] not in fold['dev_sources']
 assert all(a[k]==b[k] for k in ['source_id','target_array_sha256','normalization','normalization_source','raw'])
 pa,ta,sa=arrays(B/'real_data_qc_v1'/a['point_path'],a,8192);pb,tb,sb=arrays(B/'real_data_qc_v1'/b['point_path'],b,16384)
 assert ta==tb and pa==pb[:8192*3*4]
 rows.append(dict(case_id=cid,source_id=b['source_id'],point_path=b['point_path'],bytes=sb,sha256=b['sha256'],target_array_sha256=sha(tb),target_bytes_equal=True,input8192_is_prefix=True));total+=sb
pair=dump('paired315_data_verification_v1.json',dict(status='PASS_FOLD_D315_TARGET_PREFIX_AND_SOURCE_PAIRS',train_cases=315,train_sources=63,dev_sources_excluded=21,confirmation_sources_excluded=20,
 train_allowlist_sha256=fold['train_allowlist_sha256'],payload_bytes_16384=total,case_rows=rows,all_targets_byte_identical=True,all8192_inputs_are_16384_prefixes=True,data_regenerated=False,dev_payloads_read=0,confirmation_payloads_read=0))
order=D/'shared_order_foldD_seed0_v1.json';assert sha(raw(order))==q['order_plan']['sha256']=='4f68edd55912be0dccfb3d2a1cc72e499d3d499a36aa5f3788550145b3095720'
oldcp=D/'implementation_v1/bcsp_training_contract_foldD_8192_v5.py';oldentry=D/'implementation_v1/bcsp_training_entry_foldD_8192_v7.py'
assert sha(raw(oldcp))==q['implementation']['contract']['sha256'] and sha(raw(oldentry))==q['implementation']['entry']['sha256']
cp=I/'bcsp_training_contract_foldD_16384_v6.py';text=raw(oldcp).decode()
old="require(q['fold'] == 'D' and q['n_input'] == 8192, 'Fold D 8k arm only')";new="require(q['fold'] == 'D' and q['n_input'] == 16384, 'Fold D 16k arm only')"
assert text.count(old)==1;text=text.replace(old,new)
with cp.open('x',encoding='utf-8',newline='\n') as f:f.write(text)
ep=I/'bcsp_training_entry_foldD_16384_v8.py';text=raw(oldentry).decode().replace(oldcp.name,cp.name).replace(sha(raw(oldcp)),sha(raw(cp)))
with ep.open('x',encoding='utf-8',newline='\n') as f:f.write(text)
for p in [ep,cp]:compile(raw(p),str(p),'exec')
CODE=q['implementation']['entry']['path'].rsplit('/',1)[0]
q['n_input']=16384;q['run_id']='bcsp_geov1_b0_foldD_in16384_out8192_seed0_train_v1'
q['data_root']='/home/jovyan/adapointr_work/PoinTr/data/bcsp_geov1_foldd_16384_seed0_v1'
q['output']='/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldD_in16384_out8192_seed0_train_v1'
q['launch_attempt']=CODE+'/control_train_foldD_16384_v1/launch_attempt_v1.json'
q['implementation']['entry']=remote(ep,CODE+'/'+ep.name);q['implementation']['contract']=remote(cp,CODE+'/'+cp.name)
qualified=load(D/'qualified_data_qc_foldD_8192_v1.json');qualified['n_input']=16384;qualified['manifest_sha256']=q['QC']['manifests']['16384']['sha256']
qual=dump('qualified_data_qc_foldD_16384_v1.json',qualified);q['QC']['qualified_receipt']=remote(qual,CODE+'/evidence/'+qual.name)
candidate=dump('training_entry_request_candidate_v1.json',q)
text=(D/'controller_template_foldD_8192_v1.py').read_text()
changes=[("q['n_input'] == 8192","q['n_input'] == 16384"),("qualified['n_input'] == 8192","qualified['n_input'] == 16384"),("q['QC']['manifests']['8192']","q['QC']['manifests']['16384']"),("r['n_input'] == r['n_target'] == 8192","r['n_input'] == 16384 and r['n_target'] == 8192"),('payload_bytes == 49417378','payload_bytes == '+str(total))]
for a,b in changes:assert text.count(a)==1;text=text.replace(a,b)
template=N/'controller_template_foldD_16384_v1.py'
with template.open('x',encoding='utf-8',newline='\n') as f:f.write(text)
tree=ast.parse(text);pred={x.args[1].value:x.args[0] for x in ast.walk(tree) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='need' and len(x.args)==2 and isinstance(x.args[1],ast.Constant) and isinstance(x.args[1].value,str)}
values=dict(q=q,scope=dict(run_id=q['run_id']),qualified=qualified,r=records['16384'][ids[0]],counts={s:5 for s in fold['train_sources']},payload_bytes=total)
def evaluate(name,v):return eval(compile(ast.Expression(pred[name]),'<D16metadata>','eval'),{},v)
for name in ['single frozen run','qualified QC exact paths','training data metadata','fixed315 payload bytes/sources']:assert evaluate(name,values)
v=copy.deepcopy(values);v['q']['n_input']=8192;assert not evaluate('single frozen run',v)
v=copy.deepcopy(values);v['r']['n_target']=16384;assert not evaluate('training data metadata',v)
v=copy.deepcopy(values);v['payload_bytes']-=1;assert not evaluate('fixed315 payload bytes/sources',v)
assert q['order_plan']==baseq['order_plan'] and q['static_config']==baseq['static_config'] and q['identity']==baseq['identity']
dump('candidate_static_review_v1.json',dict(status='PASS_FOLD_D16_MINIMAL_ADAPTATION',contract_change='Only D8192 toD16384 gate and error text',entry_change='Sibling contract filename/SHA only',
 FoldD_order_reused=bind(order),FoldD8_formal_audit=bind(audit),target8192_static_model_runtime_backend_numeric_resources_unchanged=True,controller_changes=changes,controller_positive_predicates=4,controller_negative_predicates=3,
 paired_data=bind(pair),candidate_request=bind(candidate),files=[bind(ep),bind(cp),bind(template)],server_writes=0,model_calls=0))
print(json.dumps(dict(status='FOLD_D16_CANDIDATES_PREPARED_CPU_CONTRACTS_PENDING',paired_cases=315,payload_bytes=total,order_reused=True,server_writes=0)))
