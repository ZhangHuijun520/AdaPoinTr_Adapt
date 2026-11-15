"""Finite Static_D preparation: local frozen evidence + one read-only hardware identity query."""
from pathlib import Path
import ast,base64,hashlib,json,shlex,subprocess,zlib
R=Path(__file__).resolve().parent.parent;O=R/'outputs/scq_rf_Static_D_request_preparation_20261115_v1'
def read(p):return json.loads(p.read_bytes())
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def emit(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,ensure_ascii=False,allow_nan=False)
SB=R/'outputs/scq_rf_Sref_D_implementation_20261114_v1';RB=R/'outputs/scq_rf_Requery_D_implementation_20261115_v1'
rq=read(RB/'pending_transport_v1/payload/SCQ_RF_Requery_D_training_execution_request_v1.json')
sa_path=SB/'post_training_freeze_v1/freeze_verification_v1.json';ra_path=RB/'post_training_freeze_v2/freeze_verification_v1.json';sa=read(sa_path);ra=read(ra_path)
assert sa['status']=='FORMAL_SCQ_RF_SREF_POST_TRAINING_FREEZE_AUDIT_PASS' and sa['check_count']==30 and all(sa['checks'].values())
assert ra['status']=='FORMAL_RF_REQUERY_D_TRAINING_PAIR_FREEZE_AUDIT_PASS' and ra['check_count']==43 and all(ra['checks'].values())
assert sa['fold']==ra['fold']=='D' and sa['identity']==ra['identity']==rq['identity'] and ra['audit_identity']['hostname']=='shu-common-25721452-notebook-qx2k0r-0'
assert sa['order_sha256']==ra['order_sha256']=='2c9f3e9afb2cfe9ae46c0566bdbced465c64acc2a564654914d2163d74e5e838'
CB=R/'outputs/scq_rf_Static_C_implementation_20261114_v1';entry=CB/'bcsp_scq_rf_Static_C_training_entry_v1.py';bridge=CB/'bcsp_scq_rf_Static_C_training_bridge_v1.py';src=entry.read_text(encoding='utf-8')
assert "q['fold']=='C'" in src and "pair['FoldC']" in src and "fold='C'" in src and "require(torch.equal(info['N0'],info['N1'])" in src
assert "['fold']" not in bridge.read_text(encoding='utf-8')
code='''from pathlib import Path
import socket,os,subprocess,json,shutil,hashlib
assert socket.gethostname()=='shu-common-25721452-notebook-qx2k0r-0' and os.getuid()==1000
p=Path('/home/jovyan/adapointr_work/PoinTr');assert p.is_dir() and p.resolve()==p
q=p/'third_party/bcsp_scq_rf_Requery_D_training_20261115_v1/SCQ_RF_Requery_D_training_execution_request_v1.json'
assert q.stat().st_size==45310 and not q.is_symlink() and hashlib.sha256(q.read_bytes()).hexdigest()=='4a79f67d7ce29b453343d9bedc27841030d4c6223eb7bfe02d3af1d1bed9f6ed'
g=subprocess.check_output(['nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total,memory.used','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
python=Path('/opt/conda/envs/adapointr-mamba/bin/python3.10');assert python.is_file()
version=subprocess.check_output([str(python),'-I','-S','-B','-c','import sys;print(sys.version.split()[0])'],text=True,timeout=10).strip()
print(json.dumps(dict(status='STATIC_D_CURRENT_RESOURCE_IDENTITY_READONLY',hostname=socket.gethostname(),uid=os.getuid(),GPU=[x.strip() for x in g.split(',')],python_realpath=str(python.resolve()),python_version=version,free_disk_bytes=shutil.disk_usage(p).free,server_writes=0,CUDA_context=0,new_forward=0)))
'''
ast.parse(code);blob=base64.b64encode(zlib.compress(code.encode(),9)).decode();cmd=shlex.join(['/usr/bin/python3','-I','-S','-B','-c','import zlib,base64;exec(zlib.decompress(base64.b64decode('+repr(blob)+')))']);assert len(cmd.encode())<=2048
import sys
if '--static' in sys.argv:
 O.mkdir();emit(O/'scope_v1.json',dict(status='LOCAL_METADATA_AND_ONE_READONLY_RESOURCE_CALL',server_calls=1,max_call_seconds=30,max_files_read=1,max_content_bytes=45310,command_bytes=len(cmd.encode()),production_edits=0,CUDA=0,controller_sha256=rec(Path(__file__))['sha256']))
 print('STATIC_D_READONLY_REVIEW_SCOPE_FROZEN');sys.exit(0)
assert read(O/'scope_v1.json')['controller_sha256']==rec(Path(__file__))['sha256']
x=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','30','--',cmd],capture_output=True,timeout=45)
for name,b in [('stdout',x.stdout),('stderr',x.stderr)]:
 with (O/('resource_'+name+'.bin')).open('xb') as f:f.write(b)
assert x.returncode==0,(x.returncode,x.stdout.decode(errors='replace')[-1000:])
v=json.loads(x.stdout);emit(O/'current_resource_identity_v1.json',v)
old=ra['identity'];same_gpu=v['GPU'][:4]==[old['gpu_uuid'],old['gpu_name'],old['driver_version'],str(old['nvidia_smi_memory_total_MiB'])]
scope=dict(status='DRAFT_NOT_EXECUTION_REQUEST',arm='RF-Static',fold='D',seed=0,n_input=8192,n_output=8192,total_parameters=40827847,RF_parameters=231171,train_cases=315,train_sources=63,updates=3900,traversals=100,exposures=31200,drops=300,QC=rq['QC'],order_plan=rq['order_plan'],data_root=rq['data_root'],initialization=rq['initialization'],rf_initialization=rq['rf_initialization'],resources=rq['resources'],pair_contract=rq['pair_contract'],same_fold_initialization_reference=ra['initialization'],same_fold_Sref_freeze=rec(sa_path),same_fold_Requery_freeze=rec(ra_path),checkpoint_warmstart=False)
review=dict(status='STATIC_D_PREPARATION_REVIEW_COMPLETE_NO_EXECUTION_REQUEST',scope=scope,entry=rec(entry),reusable_fold_neutral_bridge=rec(bridge),training_reference_identity=old,current_observed_resource=v,same_physical_GPU_and_driver=same_gpu,hostname_changed=v['hostname']!=old['hostname'],current_stack_not_fully_reverified=True,
 next_minimal_scope=['Static_D entry: D-fold gate/identifiers; bind Sref_D and Requery_D freezes and exact full initial model state; reuse original model/bridge/runtime.','Current-container identity adapter must preserve original training identities and require exact permitted resource binding, not silently change old request/expectations.','Targeted artificial CPU batch + P3; retain Static N0 reuse, Q1 relative geometry, full source/initializer exact reads and traceback; no GPU preflight repeat.','Only after device-condition decision and final implementation hashes create pending training request; do not start training.'],
 device_decision=('Same physical GPU/driver observed; new hostname still needs explicit versioned execution-identity adaptation.' if same_gpu else 'GPU UUID or driver differs from trained D pair; disclose device confounding and obtain a scientific continuation decision before accepting migration.'),production_edits=0,CPU_tests=0,server_writes=0,new_forward=0,execution_request_created=False)
emit(O/'Static_D_scope_and_compatibility_v1.json',review)
with (O/'RF_Static_D_准备核对与最小范围_zh_v1.md').open('x',encoding='utf-8') as f:f.write('''# RF-Static Fold D 准备核对与最小范围

2026-11-15。已绑定S-ref_D（30项通过）和Requery_D（43项通过）的正式冻结证据。D折315病例、63来源、完整顺序及3900步合同沿用不变；不依据训练loss调参。

当前Static入口仍限定C折，需要新增D入口；Static bridge功能与fold无关，可以复用。模型公式、RF头、两份初始化、优化器、loss和runtime均保持不变。最终模型40,827,847参数；从头初始化，不加载已有checkpoint。

最后一组必须绑定同折Requery_D的完整初始参数/持久状态及顺序证据，并保留Static复用N0、在Q1重算相对几何的唯一机制合同。下一次集中实施只需D入口、必要的身份接口适配、一批人工CPU验证及P3，不重复GPU准入。

容器现已变为qx2k0r-0；先前五组的训练身份仍为zbpgzu-0。此次仅一次有界只读资源查询：不加载CUDA模型、不修改环境、不部署、不训练。实际GPU/驱动/解释器版本及磁盘记录在current_resource_identity_v1.json；是否与历史物理GPU及驱动一致见Static_D_scope_and_compatibility_v1.json。新容器不能自动当作原训练设备，旧审计身份不回写。

'''+review['device_decision']+'\n\n完整软件/provider资产尚未做本轮执行前核验；任何最终request仍保持待授权，不代表已经具备训练准入。本次未修改生产实现或创建执行内容。\n')
print(json.dumps(dict(status=review['status'],same_GPU_driver=same_gpu,current_GPU=v['GPU'],output=str(O))))
