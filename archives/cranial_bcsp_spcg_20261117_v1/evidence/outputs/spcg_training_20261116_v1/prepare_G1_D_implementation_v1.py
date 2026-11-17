"""Local isolated G1_D adaptation; freeze one targeted CPU batch before running it."""
from pathlib import Path,PurePosixPath
import ast,json,hashlib
S=Path(__file__).resolve().parent;W=S.parents[1];P=S/'G1_C_implementation_v1';V=S/'G1_D_implementation_v1';V.mkdir()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def rec(p,target=None):return dict(path=target or str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def emit(n,d):
 with (V/n).open('x',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2)
def write(n,s):
 ast.parse(s)
 with (V/n).open('x',encoding='utf-8',newline='\n') as f:f.write(s)
entry=(P/'bcsp_spcg_G1_C_training_entry_v1.py').read_text(encoding='utf-8')
for a,b in [('G1_C','G1_D'),('G1C','G1D'),('G0_C','G0_D'),("('G1','C',0,8192,8192)","('G1','D',0,8192,8192)"),("('G0','C',0,3900,100,31200,300)","('G0','D',0,3900,100,31200,300)"),("q['QC']['fold_binding'],'C',8192)","q['QC']['fold_binding'],'D',8192)"),("arm='G1',fold='C'","arm='G1',fold='D'")]:
 assert a in entry,a;entry=entry.replace(a,b)
marker="    for r in [q['probe_asset'],q['head_initialization'],q['mother_source']]:exact(r)"
assert entry.count(marker)==1
entry=entry.replace(marker,"    need(q['data_root']==q['project']+'/data/bcsp_geov1_foldd_8192_seed0_v1' and PurePosixPath(q['order_plan']['path']).name=='shared_order_foldD_seed0_v1.json','D data and order')\n"+marker)
write('bcsp_spcg_G1_D_training_entry_v1.py',entry)
bridge=(P/'bcsp_spcg_G1_C_training_bridge_v1.py').read_text(encoding='utf-8');assert bridge.count("q['fold']=='C'")==1;bridge=bridge.replace("q['fold']=='C'","q['fold']=='D'");write('bcsp_spcg_G1_D_training_bridge_v1.py',bridge)
q=read(S/'G1_D_preparation_v1/G1_D_training_contract_draft_v1.json');root=str(PurePosixPath(q['required_new_implementation']['entry']).parent)
q.update(schema='bcsp-spcg-G1D-training-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',execution_authorized=False)
q['launch_contract']=q.pop('planned_launch_contract');q.pop('required_new_implementation')
baseline=S/'G0_D_implementation_v1/post_training_freeze_v1/formal_freeze_result_v1.json';q['G0_D_freeze']=rec(baseline,root+'/G0_D_formal_training_freeze_v1.json')
for k in ['entry','bridge']:q['implementation'][k]=rec(V/('bcsp_spcg_G1_D_training_'+k+'_v1.py'),root+'/bcsp_spcg_G1_D_training_'+k+'_v1.py')
q['P3']=dict(path=root+'/training_P3_v1.json',bytes=0,sha256='0'*64)
emit('draft_G1_D_request_v1.json',q)
aliases=read(S/'G2_C_implementation_v1/local_metadata_map_v1.json');g0aliases=read(S/'G0_D_implementation_v1/local_metadata_map_v1.json');aliases.update(g0aliases)
aliases[q['G0_D_freeze']['path']]=str(baseline)
for k in ['entry','bridge']:aliases[q['implementation'][k]['path']]=str(V/('bcsp_spcg_G1_D_training_'+k+'_v1.py'))
required=[*q['implementation'].values(),q['CUDA_freeze'],q['G0_D_freeze'],q['static_config'],q['order_plan'],q['probe_asset'],q['head_initialization'],q['mother_source'],q['QC']['qualified_receipt'],q['QC']['verification'],q['QC']['fold_binding'],*q['QC']['manifests'].values()]
for r in required:
 a=rec(Path(aliases[r['path']]));assert (a['bytes'],a['sha256'])==(r['bytes'],r['sha256']),r['path']
emit('local_metadata_map_v1.json',aliases)
fixed=[P/'bcsp_spcg_G1_C_training_entry_v1.py',P/'bcsp_spcg_G1_C_training_bridge_v1.py',W/'outputs/spcg_implementation_20261116_v1/bcsp_spcg_head_v1.py',W/'outputs/spcg_implementation_20261116_v1/bcsp_spcg_factory_v1.py',W/'outputs/spcg_implementation_20261116_v1/bcsp_spcg_runtime_v1.py'];emit('unchanged_inputs_v1.json',[rec(p) for p in fixed])
scope=read(P/'CPU_scope_v1.json');scope['status']='FROZEN_BEFORE_SINGLE_G1D_CPU_BATCH';scope['checks']=[x.replace('G1C','G1D').replace('G0 freeze','G0_D freeze') for x in scope['checks']]+['complete authorize actual D315 metadata order100','wrong C fold and C data/order rejected','G0_D proof wrong hash rejected','G1 global256 summary direct-Q formula retained','actual optimizer groups for head and SSM exemptions','G1_D bridge lifecycle inherited exact G0_D body and frozen source unchanged'];emit('CPU_scope_v1.json',scope)
test=(P/'test_G1_C_CPU_v1.py').read_text(encoding='utf-8')
for a,b in [('G1_C','G1_D'),('SPCG_G1C','SPCG_G1D'),('G0_C_freeze','G0_D_freeze'),("q['fold']=='C'","q['fold']=='D'"),('UTC_order_hotfix_v3/post_training_freeze_v3/formal_freeze_result_v3.json','G0_D_implementation_v1/post_training_freeze_v1/formal_freeze_result_v1.json'),('shared_order_foldC_seed0_v1.json','shared_order_foldD_seed0_v1.json')]:test=test.replace(a,b)
test=test.replace('SPCG_G1_D_training_entry','SPCG_G1_D_training_entry')
# Compare only the deliberate fold change with the validated G1_C bridge.
old="bridge.read_text(encoding='utf-8').replace(\"q['arm']=='G1'\",\"q['arm']=='G0'\")==(S/'bcsp_spcg_training_bridge_v1.py').read_text(encoding='utf-8')"
new="bridge.read_text(encoding='utf-8').replace(\"q['fold']=='D'\",\"q['fold']=='C'\")==(S/'G1_C_implementation_v1/bcsp_spcg_G1_C_training_bridge_v1.py').read_text(encoding='utf-8')"
assert old in test;test=test.replace(old,new)
extra="""  aliases=json.loads((V/'local_metadata_map_v1.json').read_text(encoding='utf-8'))
  def mapped(r):
   if r['path']==q['P3']['path']:return fakep3
   if r['path'] in aliases:
    p=Path(aliases[r['path']]);a=rec(p);assert (a['bytes'],a['sha256'])==(r['bytes'],r['sha256']);return p
   return originalexact(r)
  oldsource=e.source
  def source_alias(n,r):
   mod=oldsource(n,r)
   if n=='bcsp_training_contract_v1':mod.exact=mapped
   return mod
  e.exact=mapped;e.source=source_alias
  qp=O/'request_fixture.json';qp.write_text(json.dumps(q),encoding='utf-8');ap=O/'auth_fixture.json';ap.write_text(json.dumps(dict(a,request_sha256=rec(qp)['sha256'])),encoding='utf-8');rp=O/'runtime_fixture.json';rp.write_text(json.dumps(dict(runtime,request_sha256=rec(qp)['sha256'],authorization_sha256=rec(ap)['sha256'])),encoding='utf-8')
  authorized,static,selected,fold,plan=e.authorize(rec(qp),rec(ap),rec(rp))
  check(17,authorized==q and len(selected)==315 and len(fold['train_sources'])==63 and len(plan['epochs'])==100)
  bad=copy.deepcopy(q);bad['fold']='C';data=copy.deepcopy(q);data['data_root']=data['data_root'].replace('foldd','foldc');wrongorder=copy.deepcopy(q);wrongorder['order_plan']['path']=wrongorder['order_plan']['path'].replace('foldD','foldC')
  check(18,all(reject(lambda x=x:e.validate(x,'a'*64,a,'b'*64,runtime)) for x in [bad,data,wrongorder]))
  bad=copy.deepcopy(q);bad['G0_D_freeze']['sha256']='0'*64;check(19,reject(lambda:e.validate(bad,'a'*64,a,'b'*64,runtime)))
  ss=torch.randn(1,256,3);ff=torch.randn(1,256,384);zz=torch.randn(1,1024);desc,detail=m.base_model.spcg_head.describe(D,ss,ff,zz)
  normalized=torch.nn.functional.layer_norm(ff,(384,),weight=None,bias=None,eps=1e-5).mean(1)[:,None].expand(-1,256,-1)
  check(20,detail['index'] is None and torch.equal(desc[:,:,1024:1408],normalized) and torch.equal(m.base_model.spcg_head(D,ss,ff,zz),m.base_model.spcg_head.net(desc)))
  groupfn=next(n for n in ast.parse(life.read_text(encoding='utf-8')).body if isinstance(n,ast.FunctionDef) and n.name=='optimizer_groups');ns=dict(require=e.need);exec(compile(ast.Module(body=[groupfn],type_ignores=[]),str(life),'exec'),ns);groups,rows=ns['optimizer_groups'](m);hr=[x for x in rows if x['name'].startswith('base_model.spcg_head.')]
  sentinel=nn.Linear(2,2,bias=False);sentinel.weight._no_weight_decay=True;_,sr=ns['optimizer_groups'](sentinel)
  check(21,len(hr)==6 and all(x['weight_decay']==(0 if x['name'].endswith('.bias') else .0005) for x in hr) and sr[0]['weight_decay']==0 and sr[0]['reason']=='explicit_no_weight_decay')
  g0bridge=S/'G0_D_implementation_v1/bcsp_spcg_G0_D_training_bridge_v1.py';g0cpu=json.loads((S/'G0_D_implementation_v1/CPU_batch_v1/result.json').read_text(encoding='utf-8'))
  check(22,bridge.read_text(encoding='utf-8').replace(\"q['arm']=='G1'\",\"q['arm']=='G0'\")==g0bridge.read_text(encoding='utf-8') and g0cpu['status']=='SPCG_G0_D_CPU_PASS' and g0cpu['count']==20 and g0cpu['artificial_bridge_counts']==dict(forward=3900,backward=3900) and all(rec(Path(x['path']))==x for x in json.loads((V/'unchanged_inputs_v1.json').read_text(encoding='utf-8'))))
  e.exact=originalexact;e.source=oldsource
"""
test=test.replace("  (O/'result.json').write_text",extra+"  (O/'result.json').write_text").replace('PASS16_G1_CPU_NO_SERVER','PASS22_G1D_CPU_NO_SERVER')
test=test.replace('Inherited training lifecycle and sourcepolicy tests reused; no3900step run.', 'Inherited G0_D artificial3900-observation bridge and sourcepolicy evidence reused; no real3900step run.').replace('CPU baseline fingerprint is artificial, production fingerprint remains CUDAadmitted frozenG1 identity.', 'CPU initial fingerprint is artificial; production remains frozen CUDA G1. Full authorize uses actual D metadata with aliases and artificial auth/P3 fixtures; no execution authority.')
write('test_G1_D_CPU_v1.py',test)
emit('S0_S1_static_review_v1.json',dict(status='PASS_READY_SINGLE_22_CPU_CHECKS',entry=rec(V/'bcsp_spcg_G1_D_training_entry_v1.py'),bridge=rec(V/'bcsp_spcg_G1_D_training_bridge_v1.py'),test=rec(V/'test_G1_D_CPU_v1.py'),server_operations=0,tests_run=0))
print('STATIC_PASS_G1D_READY22')
