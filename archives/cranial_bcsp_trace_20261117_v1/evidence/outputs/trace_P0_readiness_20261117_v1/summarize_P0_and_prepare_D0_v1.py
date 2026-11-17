# -*- coding: utf-8 -*-
"""Summarize existing P0 evidence and prepare a non-executable D0 specification."""
import hashlib,json
from pathlib import Path,PurePosixPath
from collections import Counter

R=Path(r'E:\Codex\2026-06-06\mamba-ccf-c-1-high-resolution');O=Path(__file__).resolve().parent
P=R/'outputs/spcg_native_prediction_preparation_20261117_v1/implementation_v1'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def hashfile(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b)
 return h.hexdigest()
def bind(p):return dict(path=str(p),bytes=p.stat().st_size,sha256=hashfile(p))
def emit(name,x):
 with (O/name).open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
def text(name,s):
 with (O/name).open('x',encoding='utf-8') as f:f.write(s)

q=read(P/'pending_transport_v1/payload/SPCG_sixmodel_native_execution_request_v1.json')
idx=read(P/'SPCG_sixmodel_input_index_v1.json')
casespath=R/'outputs/trace_plan_review_20261117_v1/TRACE_D0_proposed_cases_v2.json';chosen=read(casespath)['cases']
res=read(O/'P0_short_resource_v2_result.json');assets=read(O/'P0_short_assets_v2_result.json')
inputs=read(O/'P0_short_inputs_v2_result.json')['records'];weights=read(O/'P0_short_weights_v2_result.json')['records']
paths=read(O/'P0_final_paths_v1.json')
checks={}
checks['current_hostname_uid_matches_prior_Native']=res['hostname']==q['identity']['hostname'] and res['uid']==1000
checks['prior_request_fresh_hash']=res['request_sha256']=='c63ebdfc7e4315e36bb0c65b445925d5496352720fd78db80ff7ed0e5b155dcc'
for kind,rows,count in [('assets',assets['records'],18),('inputs',inputs,40),('weights',weights,4)]:
 checks[kind+'_exact_set_count']=len(rows)==count
 checks[kind+'_all_size_SHA256_match']=all(x['exists'] and not x['symlink'] and x['bytes']==x['expected']['bytes'] and x['sha256']==x['expected']['sha256'] for x in rows)
checks['weights_unchanged_during_hash']=all(x['unchanged_during_read'] for x in weights)
actual={(x['fold'],x['case_id']):x['expected'] for x in inputs};expected={(x['fold'],x['case_id']) for x in chosen}
checks['exact_40_case_set']=set(actual)==expected
checks['local_and_remote_input_hashes_agree']=all(actual[(c['fold'],c['case_id'])]['sha256']==c['point_file']['sha256'] for c in chosen)
checks['forty_unique_sources']=len({c['source_id'] for c in chosen})==40
checks['fold_type_balance']=Counter((c['fold'],c['defect_type']) for c in chosen)==Counter({(f,t):4 for f in ['C','D'] for t in ['bilateral','frontoorbital','parietotemporal','random_1','random_2']})
gpu=[x.strip() for x in res['SMI_stdout'].strip().split(',')]
checks['SMI_success']=res['SMI_rc']==0
checks['same_Native_GPU_driver']=gpu[:3]==[q['identity']['gpu_uuid'],q['identity']['gpu_name'],q['identity']['driver_version']]
checks['GPU_current_idle_snapshot']=int(gpu[4])<=256 and int(gpu[5])==0
checks['startup_free_disk_6GiB']=res['disk']['free']>=6*1024**3
checks['one_GiB_output_preserves_4GiB_free']=res['disk']['free']-1024**3>=4*1024**3
checks['new_paths_absent_safe_parents']=len(paths)==2 and all(not x['exists'] and x['parent_exists'] and not x['symlink'] for x in paths)
checks['Python_binary_exists_not_imported']=res['python_exists']
checks['Mamba_CUDA_binaries_stat_only']=all(r['exists'] and r['actual_bytes']==r['bytes'] for r in assets['CUDA_binaries'])
checks['unique_first_coarse_insertion']=assets['mother_forward'].count('learned_coarse = self.coarse_pred(global_feature).reshape(bs, -1, 3)')==1

scorereq=read(R/'outputs/spcg_score_implementation_20261117_v1/SPCG_local_scoring_execution_request_v1.json')
archive=scorereq['archive_inputs']['SPCG']['archive'];ap=Path(archive['path'])
checks['local_historical_prediction_archive_fresh_hash']=ap.is_file() and ap.stat().st_size==archive['bytes'] and hashfile(ap)==archive['sha256']
checks['prediction_sidecars_fresh_hash']=all(Path(s['path']).is_file() and Path(s['path']).stat().st_size==s['bytes'] and hashfile(Path(s['path']))==s['sha256'] for s in scorereq['archive_inputs']['SPCG']['sidecars'])
scorepath=R/'outputs/spcg_score_implementation_20261117_v1/unified_scores_v1/case_metrics.jsonl'
scorekeys=set()
with scorepath.open(encoding='utf-8') as f:
 for line in f:
  row=json.loads(line);scorekeys.add((row['fold'],row['case_id'],row['arm']))
checks['80_historical_score_rows_present']=all((c['fold'],c['case_id'],arm) in scorekeys for c in chosen for arm in ('G1','G2'))
assert all(checks.values()),[k for k,v in checks.items() if not v]
roleorder=['G1_C','G2_C','G1_D','G2_D']
runs={x['label']:x for x in idx['runs'] if x['label'] in roleorder}
records=[]
for label in roleorder:
 for c in chosen:
  if c['fold']!=runs[label]['fold']:continue
  records.append(dict(run=label,arm=runs[label]['arm'],fold=c['fold'],case_id=c['case_id'],source_id=c['source_id'],defect_type=c['defect_type'],selection_stratum=c['selection_stratum'],input=actual[(c['fold'],c['case_id'])],normalization=c['normalization'],normalization_source=c['normalization_source']))
assert len(records)==80
fields={'D':'float32[8192,3]','S':'float32[256,3]','F':'float32[256,384]','z':'float32[1024]','A':'float32[256,3]','x':'float32[256,1416]','f':'float32[256,384]','mu':'float32[256,3]','rho':'float32[256,1]','tau':'float32[256,1]','Q':'float32[256,3]','P':'float32[8192,3]','G2_index':'int64[256,8]','G2_native_squared_distance':'float32[256,256]','G1_index':'ALL256; no consumed KNN8'}
scope=dict(schema='bcsp-trace-D0-preparation-scope-v1',status='READY_FOR_OBSERVER_IMPLEMENTATION_NOT_AN_EXECUTION_REQUEST',execution_authorized=False,
 plan=bind(R/'docs/cranial_bcsp_trace_20261117_v2/Cranial_BCSP_FullMamba_BCSP_TRACE_正式实验计划书_审阅修订v2_2026-11-17.md'),case_manifest=bind(casespath),
 identity=dict(hostname=res['hostname'],uid=1000,project='/home/jovyan/adapointr_work/PoinTr',gpu_uuid=gpu[0],gpu_name=gpu[1],driver_version=gpu[2],SMI_total_MiB=int(gpu[3]),python=q['identity']['python_realpath']),
 counts=dict(full_forward=80,models=4,cases=40,per_model=20,batch=1,loss=0,backward=0,optimizer_step=0,warmup=0,retry=0,BNCal=0,training=0),
 order=roleorder,checkpoints={k:runs[k]['checkpoint'] for k in roleorder},input_records=records,
 inherited_assets={k:q[k] for k in ['model_root','mother_source','static_config','preflight_scope','helper','implementation','probe_asset','head_initialization']},
 capture_fields=fields,
 capture_contract=dict(reuse_existing_head_capture=True,H_first_linear_pre_hook_captures_actual_x=True,f_slice=[1024,1408],score_observer='G2 only: one exact AST expression wrapper around the FP32 argsort input; same tensor returned without mutation; per-instance patch only; production source bytes unchanged',G1_actual_neighborhood='ALL256',new_model_forward_calls=0,architecture_change=False),
 numeric=dict(eval=True,inference_mode=True,FP32=True,TF32=False,state_and_RNG_unchanged=True,history_replay_tolerance='TRACE v2 newly proposed limits; not a claim of old cross-device certification'),
 replay=dict(normalized_rtol=2e-5,normalized_atol=2e-6,world_max_abs_mm=.01,E_J_CD_score_abs_mm=.01,E_J_cover2_abs=.001,risk_labels_unchanged=True,exact_bytes_first=True),
 resources=dict(wall_seconds=900,RSS_bytes=8*1024**3,torch_peak_bytes=20*1024**3,SMI_MiB=22528,output_bytes_including_archive_and_logs=1024**3,startup_free_bytes=6*1024**3,runtime_free_bytes=4*1024**3,approx_uncompressed_tensor_bytes=216*1024**2,guarantee='monitoring only; snapshot not future execution admission'),
 future_paths=paths,historical_prediction_archive=archive,historical_score=bind(scorepath),
 cpu_analysis=dict(uses_GPU=False,adds_forward=False,max_wall_seconds=1800,primary_nonpressure_cases={'C':17,'D':18},R_case='median native probe nearest-S distance / median S nearest-other spacing; FP64 geometry',correlation='fold-wise Spearman and defect-type-centered rank residual correlation; no new bootstrap'),
 next_implementation_files=['bcsp_trace_D0_observer_v1.py','bcsp_trace_D0_entry_v1.py','bcsp_trace_D0_analysis_v1.py','test_bcsp_trace_D0_CPU_v1.py'],
 no_execution_request_reason='Observer and actual loading-path CPU validation/P3 do not exist yet; final implementation hash cannot yet be bound.',
 GPU_binary_hash_limit='Two existing Mamba/CausalConv CUDA .so files only stat checked in P0; hashes inherited and must be revalidated by the final exact execution loader before imports. No new dependency inventory.',
 authorization_boundary='Implementation-only and CPU validation require separate scope authorization. CUDA/real D0 execution requires a final bound request and separate full-SHA authorization. No G3/training implied.')
emit('TRACE_D0_preparation_scope_v1.json',scope)
emit('P0_verification_v1.json',dict(status='P0_FINITE_DIFFERENTIAL_CHECK_PASS_NOT_EXECUTION_ADMISSION',checks=checks,counts=dict(fresh_assets=18,fresh_inputs=40,fresh_weights=4,stat_only_Mamba_CUDA_binaries=2),current_resource=res,server_new_files=0,source_modifications=0,models_loaded=0,NPZ_arrays_decoded=0,forward=0,training=0,query_history=dict(first_long_query='TIMEOUT_AFTER_85S_NO_RESULT',long_query_retried=False,residual_python_probe_absent_by_process_listing=True,subsequent_queries='four fresh fixed short queries of 811/1115/1171/951 bytes; two-path closure query; no experiment retry'),open_items=['minimal observer implementation','one CPU batch covering real loading path and observation identity','formal post-test/P3','final request hash and explicit execution authorization']))

report=f'''# TRACE P0有限差量核对与D0准备记录

日期：2026-11-17。结论：**P0有限核对通过，具备准备观察入口的条件；尚不具备执行授权或实现P3。**

## 实测结果

| 对象 | 结果 |
|---|---|
| 当前容器 | `{res['hostname']}`，uid=1000 |
| GPU／驱动 | {gpu[1]}，`{gpu[0]}`，{gpu[2]}；与原Native设备一致 |
| GPU快照 | 总显存{gpu[3]} MiB，已用{gpu[4]} MiB，利用率{gpu[5]}% |
| 磁盘余量 | {res['disk']['free']} bytes，约{res['disk']['free']/1024**3:.2f} GiB |
| 源码／配置／provider／U/H | 18个固定文件，全部新鲜大小及SHA256匹配 |
| 开发输入 | 40病例／40来源，40个文件大小及SHA256匹配；未解码数组 |
| G1_C/G2_C/G1_D/G2_D权重 | 4个最终checkpoint新鲜SHA256匹配，读取期间未变；未反序列化 |
| 历史预测归档及sidecars | 本机新鲜哈希匹配；80条对应历史评分记录存在 |
| 新安装根和新输出路径 | 均不存在，父目录存在，无路径链接 |

输入根目录必须沿用实际绑定：C开发病例位于`data/bcsp_geov1_foldd_8192_seed0_v1/points`；D开发病例位于`data/bcsp_geov1_foldc_8192_seed0_v1/points`。目录名表示历史点集生成／训练分组，不能根据后缀猜测并交换路径。

两份大型Mamba/CausalConv CUDA二进制本轮只做存在性和精确大小核对，哈希继承原冻结记录，没有新鲜重哈希或导入。最终执行仍须复用原精确加载校验；本轮不扩大依赖库存。PointNet2 provider及其二进制已包括在18个新鲜文件核验中。

磁盘满足6GiB启动、4GiB运行余量和本次1GiB产物预算；这不是对后续训练矩阵容量或未来GPU空闲的保证。每次真正执行前仍按request重验。

## 真实接口结论

母版PCTransformer在encoder之后取得`coor`、`x`，经increase_dim与max得到global_feature；唯一首次coarse赋值是`self.coarse_pred(global_feature).reshape(bs,-1,3)`。SPCG factory只将该赋值替换为`spcg_head(xyz,coor,x,global_feature)`，后续mlp_query、LQI decoder和dense路径保持。

因此D0中的S=coor、F=x、z=global_feature均可在真实head入口得到，无需改encoder或decoder。已有`head.capture`保存S/F/z/A/mu/rho/tau/index和Q，但缺少实际x、f和原生距离矩阵。

最小补齐方法：沿用现有capture；给H首层添加只读pre-hook取得实际x，f取x的[1024:1408]；仅为G2对传入argsort的原生FP32分数增加一次返回同一张量的观察包装。该包装只存在于隔离实例，不能改冻结生产源码或排序公式。不得将FP64重算的近邻次序替代实际索引。G1实际使用ALL256，不伪造8邻域。

这仍是待实施的接口设计，尚未以CPU或CUDA证明观察等价性。没有必要重复原模型GPU preflight，但须完成一次针对性CPU验证/P3，之后才能创建绑定最终实现哈希的request。

## 调用链记录

最初合并查询6755字节，85秒无回传；保留原源码、命令绑定、stdout/stderr和超时记录，不声称当时资产核验通过。随后进程快照未发现残留Python核验进程，未重发该长查询。将同一范围分为四个已静态核对的短查询（811/1115/1171/951字节），均成功返回，再补核两个原定新路径。

该现象与长命令传输问题相符，但本轮未做专门传输因果实验，不能认定唯一原因。没有模型调用失败、重训或GPU重试，不新增通用传输框架。

## D0已准备的固定范围

- G1_C→G2_C→G1_D→G2_D，各20例，总80次完整forward；8192输入／8192输出、batch1。
- loss/backward/optimizer step/warmup/BNCal/retry均为0。
- 固定40例不替换，5个既有案例单列；主要关联C=17、D=18来源。
- 全部80条保存D/S/F/z/A/x/f/mu/rho/tau/Q/P，G2另存原生FP32分数和实际KNN索引。
- 新输出`{paths[1]['path']}`；新安装根`{paths[0]['path']}`；本轮未创建它们。
- GPU阶段不读GT；历史预测重放、E/J核验及关联分析在后续本机CPU评分副本中完成。
- 资源与新TRACE重放限值见`TRACE_D0_preparation_scope_v1.json`；资源阈值不放宽。

## 剩余实施边界

建议下一次仅授权四个隔离文件：观察适配、D0短入口、CPU分析入口和人工测试文件。完成一批CPU验证及正式冻结/P3后，再生成最终待授权D0 request。本轮没有写观察实现、runtime config、launcher或execution request；没有服务器写入、模型加载、forward或训练。
'''
text('TRACE_P0_核对结论与D0准备范围_zh_v1.md',report)
emit('P0_delivery_manifest_v1.json',dict(status='P0_READONLY_EVIDENCE_AND_D0_PREPARATION_COMPLETE',verification=bind(O/'P0_verification_v1.json'),scope=bind(O/'TRACE_D0_preparation_scope_v1.json'),report=bind(O/'TRACE_P0_核对结论与D0准备范围_zh_v1.md'),evidence=[bind(p) for p in sorted(O.iterdir()) if p.is_file() and p.name!='P0_delivery_manifest_v1.json']))
print(json.dumps(dict(status='P0_PASS_D0_PREPARED_NOT_EXECUTABLE',checks=len(checks),free_GiB=res['disk']['free']/1024**3,forward=0,implementation_files_written=0),ensure_ascii=True))
