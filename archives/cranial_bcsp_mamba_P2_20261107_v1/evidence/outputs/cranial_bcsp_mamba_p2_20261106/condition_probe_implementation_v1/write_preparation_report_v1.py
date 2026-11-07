"""Freeze observed readiness and concrete upload list, without deployment."""
from pathlib import Path
import json,hashlib
S=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def bind(p):return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
a=read(S/'local_candidate_assets_v1.json');p=read(S/'local_core_P3_and_execution_gaps_v1.json');t=read(S/'artificial_cpu_batch_v1/result_v1.json')
assert t['status']=='ARTIFICIAL_CPU_CONTRACT_PASS'
for n,h in t['source_sha256'].items():assert bind(S/n)['sha256']==h
assert bind(S/'artificial_cpu_batch_v1/stdout_v1.txt')['sha256']==t['stdout_sha256']
obs=dict(status='BOUNDED_READONLY_IDENTITY_AND_PATH_PRESENCE_CHECK_COMPLETE_NOT_FINAL_READINESS',provenance='Tool stdout from this conversation, 2026-11-07; manually transcribed, not a rerun or independently raw-captured transcript',hostname='shu-common-25721452-notebook-1lvq9b-0',uid=1000,GPU_UUID='GPU-4009474d-3c21-c7a6-b03d-7b46cebafa52',GPU_name='NVIDIA GeForce RTX 4090 D',SMI_total_MiB=24564,SMI_used_MiB=1,home_available_MiB=12316,point_directories_present=['/home/jovyan/adapointr_work/PoinTr/data/bcsp_geov1_foldc_8192_seed0_v1/points','/home/jovyan/adapointr_work/PoinTr/data/bcsp_geov1_foldd_8192_seed0_v1/points'],historical_checkpoint_paths_missing=[r['historical_server_checkpoint']['path'] for r in a['runs']],python_present='/opt/conda/envs/adapointr-mamba/bin/python3.10',python_observed_bytes=17331920,driver_and_dependency_bindings_complete=False,point_payload_hashes_on_server_checked=False,weights_loaded=False,forward_calls=0,server_writes=0,WSL_sandbox_E_ACCESSDENIED_then_approved_nonadmin_readonly=True)
with (S/'bounded_server_observation_v1.json').open('x',encoding='utf-8') as f:json.dump(obs,f,indent=2)
uploads=[]
for r in a['runs']:
 b=r['local_checkpoint'];uploads.append(dict(**b,suggested_upload_path='/home/jovyan/'+Path(b['path']).name,final_restore_path_not_materialized='/home/jovyan/adapointr_work/PoinTr/checkpoint_restores/condition_probe_20261107_v1/'+Path(b['path']).name))
with (S/'checkpoint_upload_list_v1.json').open('x',encoding='utf-8') as f:json.dump(dict(status='UPLOAD_LIST_ONLY_NOT_INSTALL_AUTHORIZATION',files=uploads,source_folder=str(Path(uploads[0]['path']).parent)),f,indent=2)
lines=['# 冻结特征读出对照：本机实施、验证与缺口记录 v1','','日期：2026-11-07。状态：**核心CPU验证通过，完整执行接入／最终P3尚未通过，无execution request。**','','## 已完成','','- 新增独立提取核心：从实际coarse头捕获1024维特征和256点Q，专用退出跳过decoder；不改生产源码。','- 新增固定18维几何、4维经验矩、训练来源等权ridge与四种对照；lambda=1按平均损失定义，无调参。','- 唯一一批20项人工CPU检查通过，0失败／0错误；实际CPU Torch hook输出与同一head直接计算精确一致，异常透传、hook清理、状态／RNG保持、primal／dual系数、315／105完整读者及训练／开发隔离均验证。','- 四个本机checkpoint、420个唯一8k点集文件实际SHA256核对通过。仅字节读取，未解码真实点集或加载checkpoint。','- 新容器身份、磁盘／SMI资源及固定路径存在性只读核对完成；四个冻结旧权重路径缺失。','','## 不能省略的剩余接入','','必须把已验证核心接入既有加载／数值／资源／授权短入口，增加限定的实际orchestration人工检查与最终P3；绑定新容器实际provider和数据哈希，固定运行超时与显存阈值后，才能创建待授权request。本轮没有通过不完整入口虚报P3。不会为此扩展库存框架或重复GPU preflight。','','## 权重上传清单','','四文件均位于 `E:/ResearchBackups/AdaPoinTr/BCSP_MAMBA_P1/2026-11-06_P1_checkpoints_v1/weights`。建议手动上传至`/home/jovyan/`；上传不代表授权安装／加载。最终应恢复到新目录，不能假定旧logs路径仍在。','','| 文件名 | bytes | SHA256 |','|---|---:|---|']
for b in uploads:lines.append(f"| {Path(b['path']).name} | {b['bytes']} | `{b['sha256']}` |")
lines+=['','## 科研范围仍固定','','T0/M0×C/D，各315训练＋105开发，共1680次encoder/coarse前缀，0次完整dense forward、backward或optimizer step。训练标签只用于CPU读出拟合；开发只评价。无新seed、病例选择、正则扫描、模型训练或H2选择。','', '人工核心检查不代表真实Mamba/CUDA或新容器执行链已验证。当前未产生任何真实探针对照结果。']
report=S/'冻结特征读出对照_本机准备与上传说明_zh_v1.md'
with report.open('x',encoding='utf-8') as f:f.write('\n'.join(lines)+'\n')
files=[p for p in S.iterdir() if p.is_file()]+[S/'artificial_cpu_batch_v1/result_v1.json',S/'artificial_cpu_batch_v1/stdout_v1.txt']
with (S/'preparation_delivery_manifest_v1.json').open('x',encoding='utf-8') as f:json.dump(dict(status='LOCAL_CORE_VALIDATED_FINAL_ENTRY_PENDING',files=[bind(p) for p in files],server_deployed=False,execution_request_created=False),f,indent=2)
print(json.dumps(dict(status='LOCAL_CORE_VALIDATED_FINAL_ENTRY_PENDING',tests=20,uploads=uploads,report=str(report)),ensure_ascii=True))
