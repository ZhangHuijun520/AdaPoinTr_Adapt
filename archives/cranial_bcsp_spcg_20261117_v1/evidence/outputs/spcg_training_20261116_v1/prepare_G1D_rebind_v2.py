from pathlib import Path,PurePosixPath
import json,hashlib,ast
S=Path(__file__).resolve().parent;P=S/'G1_D_implementation_v1';V=S/'G1_D_rebind_v2';V.mkdir()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def rec(p,target=None):return dict(path=target or str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def emit(n,d):
 with (V/n).open('x',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2)
def write(n,s):
 ast.parse(s)
 with (V/n).open('x',encoding='utf-8') as f:f.write(s)
old=read(P/'pending_transport_v1/payload/SPCG_G1_D_training_execution_request_v1.json');q=json.loads(json.dumps(old));oldroot=str(PurePosixPath(q['implementation']['entry']['path']).parent);root=oldroot[:-2]+'v2';oldrun=q['run_id'];run=oldrun[:-2]+'v2'
q['identity']['hostname']='shu-common-25721452-notebook-yxwd3w-0';q['identity']['gpu_uuid']='GPU-4b19574a-832d-b4fe-e655-a57462954d6a';q['environment']['CUDA_VISIBLE_DEVICES']=q['identity']['gpu_uuid'];q['run_id']=run;q['output']=q['output'].replace(oldrun,run)
q['launch_contract']={k:v.replace(oldroot,root).replace(oldrun,run).replace('SPCG_G1_D_training_execution_request_v1','SPCG_G1_D_training_execution_request_v2') for k,v in q['launch_contract'].items()}
migration=dict(schema='spcg-G1D-resource-rebind-v2',accepted=True,hostname=q['identity']['hostname'],gpu_uuid=q['identity']['gpu_uuid'],G0_D_same_device=False,G1_D_G2_D_same_device_required=True,original_request_sha256=rec(P/'pending_transport_v1/payload/SPCG_G1_D_training_execution_request_v1.json')['sha256'])
q['resource_migration']=migration;q['startup_free_disk_bytes']=6*1024**3;q['capacity']['fold_block_required_GiB']=6;q['capacity']['rationale']='Per-run output<=1GiB; preserve runtime free disk>=4GiB; startup6GiB includes margin; shared storage may change.'
q['readiness']='Before installation recheck yxwd3w GPU selector, >=6GiB available disk, uploads/reused exact hashes/D315 inputs/new targets. Cross-device G0_D comparison disclosed; no same-device claim.'
entry=(P/'bcsp_spcg_G1_D_training_entry_v1.py').read_text(encoding='utf-8')
entry=entry.replace('def validate(q,digest,a,ah,r):',"STARTUP_FREE_BYTES=6*1024**3\nRESOURCE_MIGRATION="+repr(migration)+"\n\ndef check_startup_free_disk(free):\n    need(free>=STARTUP_FREE_BYTES,'startup disk >=6GiB')\n\ndef validate(q,digest,a,ah,r):\n    need(q.get('resource_migration')==RESOURCE_MIGRATION and q.get('startup_free_disk_bytes')==STARTUP_FREE_BYTES,'frozen migration and startup budget')\n    need(q['identity']['hostname']==RESOURCE_MIGRATION['hostname'] and q['identity']['gpu_uuid']==RESOURCE_MIGRATION['gpu_uuid'],'rebound identity')")
assert entry.count("need(shutil.disk_usage(out).free>=int(8.5*1024**3),'foldblock disk')")==1
entry=entry.replace("need(shutil.disk_usage(out).free>=int(8.5*1024**3),'foldblock disk')","check_startup_free_disk(shutil.disk_usage(out).free)")
write('bcsp_spcg_G1_D_training_entry_v1.py',entry);write('bcsp_spcg_G1_D_training_bridge_v1.py',(P/'bcsp_spcg_G1_D_training_bridge_v1.py').read_text(encoding='utf-8'))
for k in ['entry','bridge']:q['implementation'][k]=rec(V/('bcsp_spcg_G1_D_training_'+k+'_v1.py'),root+'/bcsp_spcg_G1_D_training_'+k+'_v1.py')
q['G0_D_freeze']['path']=q['G0_D_freeze']['path'].replace(oldroot,root);q['P3']=dict(path=root+'/training_P3_v1.json',bytes=0,sha256='0'*64)
emit('draft_G1_D_request_v1.json',q)
aliases=read(P/'local_metadata_map_v1.json');aliases[q['G0_D_freeze']['path']]=aliases[old['G0_D_freeze']['path']]
for k in ['entry','bridge']:aliases[q['implementation'][k]['path']]=str(V/('bcsp_spcg_G1_D_training_'+k+'_v1.py'))
emit('local_metadata_map_v1.json',aliases);emit('unchanged_inputs_v1.json',read(P/'unchanged_inputs_v1.json'))
scope=read(P/'CPU_scope_v1.json');scope['checks']+=['accepted migration and new identity frozen','startup6GiB boundary and8.37GiB acceptance','old hostname or GPU rejected','runtime4GiB and output1GiB limits unchanged','science and non-entry scientific modules unchanged','missing migration or altered startup threshold rejected'];scope['status']='FROZEN_BEFORE_SINGLE_28_CPU_CHECKS';emit('CPU_scope_v1.json',scope)
test=(P/'test_G1_D_CPU_v1.py').read_text(encoding='utf-8')
extra="""  check(23,q['resource_migration']==e.RESOURCE_MIGRATION and q['identity']['hostname']=='shu-common-25721452-notebook-yxwd3w-0' and q['environment']['CUDA_VISIBLE_DEVICES']==q['identity']['gpu_uuid'])
  e.check_startup_free_disk(6*1024**3);e.check_startup_free_disk(8983150592)
  check(24,reject(lambda:e.check_startup_free_disk(6*1024**3-1)))
  e.exact=mapped
  bad=copy.deepcopy(q);bad['identity']['hostname']='shu-common-25721452-notebook-lwwgl9-0';gpu=copy.deepcopy(q);gpu['identity']['gpu_uuid']='GPU-c25d6be2-173c-031a-89c6-b96e0f5f8190';gpu['environment']['CUDA_VISIBLE_DEVICES']=gpu['identity']['gpu_uuid']
  check(25,reject(lambda:e.validate(bad,'a'*64,a,'b'*64,runtime)) and reject(lambda:e.validate(gpu,'a'*64,a,'b'*64,runtime)))
  check(26,e.RESOURCES['minimum_free_disk_bytes']==4*1024**3 and e.RESOURCES['output_bytes']==1024**3 and q['resources']==e.RESOURCES)
  prior=json.loads((S/'G1_D_implementation_v1/pending_transport_v1/payload/SPCG_G1_D_training_execution_request_v1.json').read_text(encoding='utf-8'))
  check(27,all(q[k]==prior[k] for k in ['science','counts','resources','static_config','QC','order_plan','data_root','probe_asset','head_initialization','mother_source','expected_initial_state_sha256','parent_G0_initial_state_sha256']) and all(v==prior['implementation'][k] for k,v in q['implementation'].items() if k not in ['entry','bridge']))
  bad=copy.deepcopy(q);bad.pop('resource_migration');budget=copy.deepcopy(q);budget['startup_free_disk_bytes']=5*1024**3
  check(28,reject(lambda:e.validate(bad,'a'*64,a,'b'*64,runtime)) and reject(lambda:e.validate(budget,'a'*64,a,'b'*64,runtime)))
  e.exact=originalexact
"""
test=test.replace("  (O/'result.json').write_text",extra+"  (O/'result.json').write_text");write('test_G1_D_CPU_v1.py',test)
emit('revision_scope_v2.json',dict(status='STATIC_PASS_READY_CPU28',old_request=rec(P/'pending_transport_v1/payload/SPCG_G1_D_training_execution_request_v1.json'),identity_evidence=rec(P/'resource_rebind_yxwd3w_readonly_v1/result.json'),migration=migration,entry=rec(V/'bcsp_spcg_G1_D_training_entry_v1.py'),bridge_unchanged=rec(V/'bcsp_spcg_G1_D_training_bridge_v1.py')['sha256']==rec(P/'bcsp_spcg_G1_D_training_bridge_v1.py')['sha256'],server_operations=0))
print('STATIC_PASS_READY_CPU28')
