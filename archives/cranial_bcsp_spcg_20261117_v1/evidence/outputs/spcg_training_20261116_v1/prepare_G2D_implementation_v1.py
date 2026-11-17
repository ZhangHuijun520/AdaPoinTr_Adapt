from pathlib import Path,PurePosixPath
import json,hashlib,ast
S=Path(__file__).resolve().parent;P=S/'G1_D_rebind_v2';V=S/'G2_D_implementation_v1';V.mkdir()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def rec(p,target=None):return dict(path=target or str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def emit(n,d):
 with (V/n).open('x',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2)
def write(n,s):
 ast.parse(s)
 with (V/n).open('x',encoding='utf-8') as f:f.write(s)
q=read(S/'G2_D_preparation_v1/G2_D_training_contract_draft_v1.json');root=str(PurePosixPath(q['required_new_implementation']['entry']).parent)
q.update(schema='bcsp-spcg-G2D-training-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',execution_authorized=False)
q['launch_contract']=q.pop('planned_launch_contract');q.pop('required_new_implementation')
q['resource_migration']['schema']='spcg-G2D-resource-continuation-v1'
g0=S/'G0_D_implementation_v1/post_training_freeze_v1/formal_freeze_result_v1.json';g1=P/'post_training_freeze_v2/formal_freeze_result_v2.json'
q['G0_D_freeze']=rec(g0,root+'/G0_D_formal_training_freeze_v1.json');q['G1_D_freeze']=rec(g1,root+'/G1_D_formal_training_freeze_v2.json')
entry=(P/'bcsp_spcg_G1_D_training_entry_v1.py').read_text(encoding='utf-8').replace('G1','G2')
line=next(x for x in entry.splitlines() if x.startswith('RESOURCE_MIGRATION='));entry=entry.replace(line,'RESOURCE_MIGRATION='+repr(q['resource_migration']))
marker="    for r in [q['probe_asset'],q['head_initialization'],q['mother_source']]:exact(r)"
entry=entry.replace(marker,"""    global_pair=bound(q['G1_D_freeze'])
    need(global_pair['status']=='FORMAL_SPCG_G1_D_POST_TRAINING_FREEZE_PASS' and all(global_pair['checks'].values()),'G1_D freeze')
    need((global_pair['arm'],global_pair['fold'],global_pair['seed'],global_pair['updates'],global_pair['traversals'],global_pair['exposures'],global_pair['drops'])==('G1','D',0,3900,100,31200,300),'G1_D pairing')
    need(global_pair['order_plan']==q['order_plan'] and global_pair['initialization_raw_tensor_fingerprint']==q['expected_initial_state_sha256'],'G1_D same order and full initial state')
    need(global_pair['pairing']['G1_D_gpu_uuid']==q['identity']['gpu_uuid'] and global_pair['request_sha256']==RESOURCE_MIGRATION['paired_G1_D_request_sha256'],'G1_D same device and request')
"""+marker)
write('bcsp_spcg_G2_D_training_entry_v1.py',entry)
bridge=(P/'bcsp_spcg_G1_D_training_bridge_v1.py').read_text(encoding='utf-8').replace("q['arm']=='G1'","q['arm']=='G2'");write('bcsp_spcg_G2_D_training_bridge_v1.py',bridge)
for k in ['entry','bridge']:q['implementation'][k]=rec(V/('bcsp_spcg_G2_D_training_'+k+'_v1.py'),root+'/bcsp_spcg_G2_D_training_'+k+'_v1.py')
q['P3']=dict(path=root+'/training_P3_v1.json',bytes=0,sha256='0'*64)
q['readiness']='Before authorized execution recheck yxwd3w GPU, startup6GiB, all reused assets/D315 inputs/order/proofs/new targets. No current server operations; G0_D remains cross-device.'
emit('draft_G2_D_request_v1.json',q)
aliases=read(P/'local_metadata_map_v1.json');aliases[q['G0_D_freeze']['path']]=str(g0);aliases[q['G1_D_freeze']['path']]=str(g1)
for k in ['entry','bridge']:aliases[q['implementation'][k]['path']]=str(V/('bcsp_spcg_G2_D_training_'+k+'_v1.py'))
emit('local_metadata_map_v1.json',aliases);emit('unchanged_inputs_v1.json',read(P/'unchanged_inputs_v1.json'))
scope=read(P/'CPU_scope_v1.json');scope['checks']=[x.replace('G1','G2') for x in scope['checks']];scope['checks'][19]='actual G2 stable k8 summary and direct Q formula';scope['checks']+=['G1_D proof hash spoof rejected','G1_D different-device proof rejected','G2 S/F/z gradients finite nonzero','same G1_D full initial state and bridge only arm difference'];scope['status']='FROZEN_BEFORE_SINGLE32_CPU_CHECKS';emit('CPU_scope_v1.json',scope)
test=(P/'test_G1_D_CPU_v1.py').read_text(encoding='utf-8').replace('G1','G2')
test=test.replace("q['CUDA_freeze']['path']:base/", "q['G1_D_freeze']['path']:S/'G1_D_rebind_v2/post_training_freeze_v2/formal_freeze_result_v2.json',q['CUDA_freeze']['path']:base/")
test=test.replace("S/'G2_D_implementation_v1/pending_transport_v1/payload/SPCG_G2_D_training_execution_request_v1.json'", "S/'G1_D_rebind_v2/pending_transport_v1/payload/SPCG_G1_D_training_execution_request_v2.json'")
test=test.replace("normalized=torch.nn.functional.layer_norm(ff,(384,),weight=None,bias=None,eps=1e-5).mean(1)[:,None].expand(-1,256,-1)", "idx=torch.argsort(((ss[:,None]-detail['A'][:,:,None]).detach()**2).sum(-1),dim=-1,stable=True)[...,:8];normalized=torch.nn.functional.layer_norm(ff,(384,),weight=None,bias=None,eps=1e-5)[torch.arange(1)[:,None,None],idx].mean(2)")
test=test.replace("detail['index'] is None", "torch.equal(detail['index'],idx) and detail['index'].shape==(1,256,8)")
extra="""  e.exact=mapped
  bad=copy.deepcopy(q);bad['G1_D_freeze']['sha256']='0'*64;check(29,reject(lambda:e.validate(bad,'a'*64,a,'b'*64,runtime)))
  proof=json.loads(Path(aliases[q['G1_D_freeze']['path']]).read_text(encoding='utf-8'));proof['pairing']['G1_D_gpu_uuid']='GPU-other';spoof=O/'wrong_device_proof.json';spoof.write_text(json.dumps(proof),encoding='utf-8');bad=copy.deepcopy(q);bad['G1_D_freeze']=rec(spoof)
  check(30,reject(lambda:e.validate(bad,'a'*64,a,'b'*64,runtime)))
  gs=torch.randn(1,256,3,requires_grad=True);gf=torch.randn(1,256,384,requires_grad=True);gz=torch.randn(1,1024,requires_grad=True);m.base_model.spcg_head(D,gs,gf,gz).square().mean().backward()
  check(31,all(x.grad is not None and bool(torch.isfinite(x.grad).all()) and float(x.grad.norm())>0 for x in [gs,gf,gz]))
  gp=json.loads(Path(aliases[q['G1_D_freeze']['path']]).read_text(encoding='utf-8'))
  check(32,gp['initialization_raw_tensor_fingerprint']==q['expected_initial_state_sha256'] and bridge.read_text(encoding='utf-8').replace(\"q['arm']=='G2'\",\"q['arm']=='G1'\")== (S/'G1_D_rebind_v2/bcsp_spcg_G1_D_training_bridge_v1.py').read_text(encoding='utf-8'))
  e.exact=originalexact
"""
test=test.replace("  (O/'result.json').write_text",extra+"  (O/'result.json').write_text").replace('PASS16_G2_DPU_NO_SERVER','PASS32_G2D_CPU_NO_SERVER')
write('test_G2_D_CPU_v1.py',test)
emit('implementation_scope_v1.json',dict(status='STATIC_PASS_READY_CPU32',entry=rec(V/'bcsp_spcg_G2_D_training_entry_v1.py'),G1_D_freeze=rec(g1),same_device_required=q['identity']['gpu_uuid'],startup_free_disk_bytes=q['startup_free_disk_bytes'],server_operations=0))
print('STATIC_PASS_READY32')
