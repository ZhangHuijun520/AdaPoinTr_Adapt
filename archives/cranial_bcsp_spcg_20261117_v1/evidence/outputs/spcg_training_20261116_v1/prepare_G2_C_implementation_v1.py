"""Create isolated G2_C candidates and freeze one CPU batch before execution."""
from pathlib import Path,PurePosixPath
import json,hashlib,ast,subprocess
S=Path(__file__).resolve().parent;W=S.parents[1];P=S/'G1_C_implementation_v1';V=S/'G2_C_implementation_v1';V.mkdir()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def rec(p,target=None):return dict(path=target or str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def emit(n,x):
 with (V/n).open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2)
def write(n,s):
 ast.parse(s)
 with (V/n).open('x',encoding='utf-8',newline='\n') as f:f.write(s)
entry=(P/'bcsp_spcg_G1_C_training_entry_v1.py').read_text(encoding='utf-8').replace('G1','G2')
marker="    for r in [q['probe_asset'],q['head_initialization'],q['mother_source']]:exact(r)"
entry=entry.replace(marker,"""    global_pair=bound(q['G1_C_freeze'])
    need(global_pair['status']=='FORMAL_SPCG_G1_C_POST_TRAINING_FREEZE_PASS' and all(global_pair['checks'].values()),'G1 freeze')
    need((global_pair['arm'],global_pair['fold'],global_pair['seed'],global_pair['updates'],global_pair['traversals'],global_pair['exposures'],global_pair['drops'])==('G1','C',0,3900,100,31200,300),'G1 pairing')
    need(global_pair['order_plan']==q['order_plan'] and global_pair['initialization_raw_tensor_fingerprint']==q['expected_initial_state_sha256'],'G1 same order and shared head initial state')
"""+marker)
assert entry.count('global_pair=')==1
write('bcsp_spcg_G2_C_training_entry_v1.py',entry)
write('bcsp_spcg_G2_C_training_bridge_v1.py',(P/'bcsp_spcg_G1_C_training_bridge_v1.py').read_text(encoding='utf-8').replace("q['arm']=='G1'","q['arm']=='G2'"))
q=read(P/'draft_G1_C_request_v1.json');oldroot=str(PurePosixPath(q['implementation']['entry']['path']).parent);root=oldroot.replace('G1C','G2C');oldrun=q['run_id'];run=oldrun.replace('G1','G2')
q['schema']='bcsp-spcg-G2C-training-v1';q['arm']='G2';q['run_id']=run;q['output']=q['output'].replace(oldrun,run)
q['launch_contract']={k:v.replace(oldroot,root).replace(oldrun,run).replace('SPCG_G1_C','SPCG_G2_C') for k,v in q['launch_contract'].items()}
for k in ['entry','bridge']:q['implementation'][k]=rec(V/('bcsp_spcg_G2_C_training_'+k+'_v1.py'),root+'/bcsp_spcg_G2_C_training_'+k+'_v1.py')
g0=S/'UTC_order_hotfix_v3/post_training_freeze_v3/formal_freeze_result_v3.json';g1=P/'post_training_freeze_v1/formal_freeze_result_v1.json'
q['G0_C_freeze']=rec(g0,root+'/G0_C_formal_training_freeze_v3.json');q['G1_C_freeze']=rec(g1,root+'/G1_C_formal_training_freeze_v1.json')
native=json.loads(read(W/'outputs/spcg_implementation_20261116_v1/output_policy_hotfix_v3/post_CUDA_freeze_v3/server_evidence.json')['output']['completion.json']['text'])
q['expected_initial_state_sha256']=native['result']['models']['G2']['initial_state_sha256']
assert q['expected_initial_state_sha256']==read(g1)['initialization_raw_tensor_fingerprint']
q['P3']=dict(path=root+'/training_P3_v1.json',bytes=0,sha256='0'*64)
emit('draft_G2_C_request_v1.json',q)
scope=read(P/'CPU_scope_v1.json');scope['status']='FROZEN_BEFORE_SINGLE_G2_CPU_BATCH';scope['checks']=[x.replace('G1','G2') for x in scope['checks']]+['G1/G2 shared complete initial state with distinct outputs','G2 exact stable k8 neighbourhood and direct nonresidual head','G2 Memory feature coordinate and global gradients finite','actual authorize path metadata source fold and100traversals','G1 proof spoof and G1 arm rejected','launcher POSIX path and one-way in-memory contract','actual optimizer grouping covers six head parameters','frozen science modules and G0/G1 source bytes unchanged'];emit('CPU_scope_v1.json',scope)
test=(P/'test_G1_C_CPU_v1.py').read_text(encoding='utf-8').replace('G1','G2')
test=test.replace("bridge.read_text(encoding='utf-8').replace(\"q['arm']=='G2'\",\"q['arm']=='G0'\")==", "bridge.read_text(encoding='utf-8').replace(\"q['arm']=='G2'\",\"q['arm']=='G0'\")==")
test=test.replace("q['G0_C_freeze']['path']:baseline,", "q['G0_C_freeze']['path']:baseline,q['G1_C_freeze']['path']:S/'G1_C_implementation_v1/post_training_freeze_v1/formal_freeze_result_v1.json',")
extra="""  # Additional G2-specific tests, same single batch, no training or data payload.
  shared=legacy();shared,_=f.install(shared,'G1',U,H,MOTHER,rec(MOTHER)['sha256']);shared.train()
  check(17,e.raw_state_fingerprint(shared)==expected and not torch.equal(shared(D)[0],ret[0]))
  ss=torch.randn(1,256,3,requires_grad=True);ff=torch.randn(1,256,384,requires_grad=True);zz=torch.randn(1,1024,requires_grad=True)
  desc,detail=m.base_model.spcg_head.describe(D,ss,ff,zz)
  expected_idx=torch.argsort(((ss[:,None]-detail['A'][:,:,None]).detach()**2).sum(-1),dim=-1,stable=True)[...,:8]
  check(18,torch.equal(detail['index'],expected_idx) and detail['index'].shape==(1,256,8) and torch.equal(m.base_model.spcg_head(D,ss,ff,zz),m.base_model.spcg_head.net(desc)))
  m.base_model.spcg_head(D,ss,ff,zz).square().mean().backward()
  check(19,all(t.grad is not None and bool(torch.isfinite(t.grad).all()) and float(t.grad.norm())>0 for t in [ss,ff,zz]))
  # Full authorize() with actual frozen metadata validators. Only path aliases and artificial P3/auth are substituted.
  aliases=json.loads((V/'local_metadata_map_v1.json').read_text(encoding='utf-8'))
  def mapped(r):
   if r['path']==q['P3']['path']:return fakep3
   p=Path(aliases[r['path']]);assert p.stat().st_size==r['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256'];return p
  oldsource=e.source
  def scoped_source(n,r):
   mod=oldsource(n,r)
   if n=='bcsp_training_contract_v1':mod.exact=mapped
   return mod
  e.exact=mapped;e.source=scoped_source
  qfixture=O/'request_fixture.json';qfixture.write_text(json.dumps(q),encoding='utf-8');af=O/'authorization_fixture.json';af.write_text(json.dumps(dict(a,request_sha256=rec(qfixture)['sha256'])),encoding='utf-8');rf=O/'runtime_fixture.json';rf.write_text(json.dumps(dict(runtime,request_sha256=rec(qfixture)['sha256'],authorization_sha256=rec(af)['sha256'])),encoding='utf-8')
  def fullmapped(r):
   if r['path'] in {str(x.resolve()) for x in [qfixture,af,rf]}:return originalexact(r)
   return mapped(r)
  e.exact=fullmapped
  authorized,static,selected,fold,plan=e.authorize(rec(qfixture),rec(af),rec(rf))
  check(20,authorized==q and len(selected)==315 and len(fold['train_sources'])==63 and len(plan['epochs'])==100)
  bad=copy.deepcopy(q);bad['expected_initial_state_sha256']='0'*64;wrong=copy.deepcopy(q);wrong['arm']='G1'
  check(21,reject(lambda:e.validate(bad,'a'*64,a,'b'*64,runtime)) and reject(lambda:e.validate(wrong,'a'*64,a,'b'*64,runtime)))
  launcher=e.render_launcher(q,'a'*64,'b'*64,'c'*64)
  check(22,all('\\\\' not in p for p in q['launch_contract'].values()) and '3600s' in launcher and q['implementation']['entry']['path'] in launcher and q['launch_contract']['runtime_path'] in launcher)
  groupfn=next(n for n in ast.parse(life.read_text(encoding='utf-8')).body if isinstance(n,ast.FunctionDef) and n.name=='optimizer_groups');ns=dict(require=lambda ok,msg:e.need(ok,msg));exec(compile(ast.Module(body=[groupfn],type_ignores=[]),str(life),'exec'),ns);groups,rows=ns['optimizer_groups'](m);headrows=[x for x in rows if x['name'].startswith('base_model.spcg_head.')]
  check(23,len(headrows)==6 and all(x['weight_decay']==(0 if x['name'].endswith('.bias') else .0005) for x in headrows))
  check(24,all(rec(Path(x['path']))==x for x in json.loads((V/'unchanged_inputs_v1.json').read_text(encoding='utf-8'))))
  e.exact=originalexact;e.source=oldsource
"""
test=test.replace("  (O/'result.json').write_text",extra+"  (O/'result.json').write_text").replace("PASS16_G2_CPU_NO_SERVER","PASS24_G2_CPU_NO_SERVER")
test=test.replace("CPU baseline fingerprint is artificial, production fingerprint remains CUDAadmitted frozenG2 identity.","CPU baseline fingerprint is artificial, production fingerprint remains CUDAadmitted frozenG2 identity. Full authorize uses real metadata validators with frozen metadata aliases and artificial auth/P3; it grants no execution authority.")
write('test_G2_C_CPU_v1.py',test)
# Resolve only exact named metadata/source records; no NPZ or checkpoint contents.
records=list(q['implementation'].values())+[q['static_config'],q['order_plan'],q['CUDA_freeze'],q['G0_C_freeze'],q['G1_C_freeze'],q['probe_asset'],q['head_initialization'],q['mother_source'],q['QC']['qualified_receipt'],q['QC']['verification'],q['QC']['fold_binding'],*q['QC']['manifests'].values()]
paths=[W/x for x in subprocess.run(['rg','--files','outputs','deliverables'],cwd=W,capture_output=True,text=True,encoding='utf-8',check=True).stdout.splitlines()]
aliases={}
for r in records:
 name=PurePosixPath(r['path']).name
 candidates=sorted([p for p in paths if p.name==name or p.name.endswith('_'+name)],key=lambda p:len(str(p)))
 if r==q['G1_C_freeze']:candidates.insert(0,P/'post_training_freeze_v1/formal_freeze_result_v1.json')
 for p in candidates:
  if not p.is_file():continue
  if p.stat().st_size==r['bytes'] and rec(p)['sha256']==r['sha256']:aliases[r['path']]=str(p.resolve());break
 else:raise ValueError('No local exact source: '+r['path'])
emit('local_metadata_map_v1.json',aliases)
fixed=[P/'bcsp_spcg_G1_C_training_entry_v1.py',P/'bcsp_spcg_G1_C_training_bridge_v1.py',W/'outputs/spcg_implementation_20261116_v1/bcsp_spcg_head_v1.py',W/'outputs/spcg_implementation_20261116_v1/bcsp_spcg_factory_v1.py',W/'outputs/spcg_implementation_20261116_v1/bcsp_spcg_runtime_v1.py']
emit('unchanged_inputs_v1.json',[rec(p) for p in fixed])
emit('S0_S1_static_review_v1.json',dict(status='PASS_READY_FOR_SINGLE_24_CHECK_CPU_BATCH',entry=rec(V/'bcsp_spcg_G2_C_training_entry_v1.py'),bridge=rec(V/'bcsp_spcg_G2_C_training_bridge_v1.py'),test=rec(V/'test_G2_C_CPU_v1.py'),local_alias_count=len(aliases),server_operations=0,CPU_batch_executed=False))
print('G2_C_STATIC_PASS_READY24')
