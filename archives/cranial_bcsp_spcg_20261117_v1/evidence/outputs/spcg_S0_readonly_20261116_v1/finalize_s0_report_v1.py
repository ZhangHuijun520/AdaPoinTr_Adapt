"""Read frozen local text/JSON and write the S0 report; no tensor/model execution."""
from pathlib import Path
import json,hashlib,collections,re
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,x):(O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
r=load(O/'S0_remote_result_v1.json');assert r['status']=='S0_REMOTE_SOURCE_HASH_AND_METADATA_PASS_NO_EXECUTION_ADMISSION'
scope=load(O/'S0_readonly_scope_v1.json');ctx=load(W/'outputs/scq_rive_training_implementation_20261115_v1/implementation_context_v1.json')
B=W/'outputs/cranial_bcsp_scq_foldC_training_preparation_20261113_v1/candidate_payload'
fold=load(B/'fold_binding.json')['folds'];manifest=[json.loads(x) for x in (B/'manifest_8192.jsonl').read_text(encoding='utf-8').splitlines()]
checks={};info={};local=[]
for a in scope['files']:
 p=Path(ctx['mirror'].get(a['path'],''))
 if a['path'].endswith('/models/AdaPoinTr.py'):p=W/'deliverables/cranial_bcsp_fullmamba_20261112_v1/public_payload/parent_source_snapshot/models/AdaPoinTr.py'
 if '/bcsp_scq_foldC_training_20261113_v1/' in a['path']:p=B/Path(a['path']).name
 if p.is_file():
  assert sha(p)==a['sha256'];local.append(dict(remote=a['path'],local=str(p),sha256=sha(p)))
checks['420_unique_cases']=len(manifest)==len({x['case_id'] for x in manifest})==420
checks['84_sources_five_defects']=len({x['source_id'] for x in manifest})==84 and all(v==5 for v in collections.Counter(x['source_id'] for x in manifest).values())
checks['8k_D_bbox_manifest']=all(x['n_input']==x['n_target']==8192 and x['normalization_source']=='defective_bbox' for x in manifest)
for f in ['C','D']:
 p=B/('shared_order_fold'+f+'_seed0_v1.json');q=load(p);tr=fold[f]['train_case_ids'];dev=fold[f]['dev_case_ids']
 checks[f+'_source_split']=len(fold[f]['train_sources'])==63 and len(fold[f]['dev_sources'])==21 and not(set(fold[f]['train_sources'])&set(fold[f]['dev_sources']))
 checks[f+'_case_split']=len(tr)==315 and len(dev)==105 and set(q['case_ids'])==set(tr)
 ok=len(q['epochs'])==100
 for i,e in enumerate(q['epochs']):
  flat=[x for b in e['batches'] for x in b];drop=e['dropped']
  ok=ok and e['epoch']==i and len(e['batches'])==39 and all(len(b)==8 for b in e['batches']) and len(flat)==len(set(flat))==312 and len(drop)==3 and not set(flat)&set(drop) and set(flat+drop)==set(tr)
 checks[f+'_3900_order_31200_exposures_300_drops']=ok
 info[f]=dict(train_sources=63,dev_sources=21,train_cases=315,dev_cases=105,traversals=100,updates=3900,exposures=31200,drops=300,order_sha256=sha(p))
checks['42_train_overlap']=len(set(fold['C']['train_sources'])&set(fold['D']['train_sources']))==42
checks['dev_disjoint']=not set(fold['C']['dev_sources'])&set(fold['D']['dev_sources'])
checks['dev_access_via_opposite_training_root']=set(fold['C']['dev_sources'])<=set(fold['D']['train_sources']) and set(fold['D']['dev_sources'])<=set(fold['C']['train_sources'])
assert all(checks.values())
ident=r['phases'][0]['result'];assert ident['available_bytes']>=8.5*1024**3
cleanup=load(W/'outputs/scq_RIVE_server_cleanup_20261116_v1/candidate_cleanup_scope_v2.json')
ck=[x for x in cleanup['files'] if str(x).find('ckpt-last.pth')>=0]
storage=dict(current_available_bytes=ident['available_bytes'],current_available_GiB=ident['available_bytes']/1024**3,proposed_fold_minimum_GiB=8.5,headroom_over_fold_bytes=ident['available_bytes']-int(8.5*1024**3),full_matrix_minimum_GiB=12.5,full_matrix_shortfall_bytes=int(12.5*1024**3)-ident['available_bytes'],per_run_output_cap_bytes=1024**3,per_run_cap_status='IMPLEMENTATION_ESTIMATE_AND_RUNTIME_ENFORCEMENT_PENDING',historical_checkpoint_entries=ck)
save('S0_local_metadata_and_boundary_review_v1.json',dict(status='S0_STATIC_METADATA_SEMANTICS_PASS_NOT_CPU_TESTS',checks=checks,folds=info,local_source_matches=local,storage=storage,model_selection='untrained LQI constructor chain, not RF/SCQ factory or restored trained checkpoint',operations=dict(tensor_tests=0,NPZ_payload_reads=0,checkpoint_loads=0,model_imports=0)))
report=f'''# BCSP-SPCG S0有限只读差量核对报告

日期：2026-11-16。依据：已确认的正式计划审阅修订v2，SHA256 `3c071175fbb6743f57c593093cc982ad0f37cce9c2041059990d2749b3ff60f1`。

**结论：S0证据足以进入限定implementation-only的范围确认；没有发现需要重建数据、恢复旧权重或扩展通用框架的阻断。尚未实施，也不构成GPU或训练准入。**

## 1. 本轮范围与实际操作

通过现有WSL＋hpc5000读取当前身份／容量及固定20个源码、元数据文件的大小和SHA256，共3,176,036bytes；630个NPZ仅lstat，不打开payload。正式远端有界核对耗时{r['seconds']:.3f}秒，所有20项匹配。此前单独hostname调用与本次身份一致。

普通受限上下文首次WSL调用返回E_ACCESSDENIED，未触及服务器文件；工具批准普通用户上下文后完成核对，没有管理员提权。没有上传、安装或修改服务器文件。未运行CPU张量测试、加载checkpoint、import模型、CUDA、forward、训练或评分。

## 2. 当前服务器与容量

| 项目 | 实测 |
|---|---|
| hostname | {ident['hostname']} |
| 用户／目录 | uid1000；/home/jovyan/adapointr_work/PoinTr |
| GPU | NVIDIA GeForce RTX4090 D，UUID GPU-c25d6be2-173c-031a-89c6-b96e0f5f8190 |
| driver／SMI | 570.190；24564MiB总显存、查询时1MiB已用 |
| 可用磁盘 | {ident['available_bytes']:,}bytes＝{ident['available_bytes']/1024**3:.3f}GiB |
| 当前服务器Git | 不是Git仓库；以本机规范仓库和冻结源码SHA为准 |

当前GPU UUID不同于RIVE训练时的UUID；不影响本轮只读判断，未来SPCG身份必须绑定当前实际设备，不沿用旧UUID。按折三臂须在同一设备条件下形成新配对块。SMI此时低占用不代表未来持续独占，也没有做宿主机PID映射。

8.5GiB按折准备预算较当前容量尚余{storage['headroom_over_fold_bytes']:,}bytes；六run同时驻留的12.5GiB方案仍缺{storage['full_matrix_shortfall_bytes']:,}bytes。采用C三臂→C块Native并归档核验→获精确清理授权或增加空间→D三臂。不得在D前依据C开发分数改方案。

**每run 1GiB仍是待实现验证的上限，不是本轮已证明的真实序列化大小。** 历史checkpoint仅作容量参照；新H、优化器状态、日志、tmp和初态快照必须合计估算。不能为了容量改变batch、点数、模型或3900步。

## 3. 未训练LQI母版已定位

沿用构造链：legacy AdaPoinTr完整CPU初始化→`bcsp_p1_model_factory_v1.build_model(...,'M0',0)`替换六层encoder→`bcsp_lqi_factory_v1.build_model`安装八层LQI decoder。实际源码与本机镜像SHA一致。

共同母版流seed0；encoder新Mamba流20261104；LQI新decoder流20261110，均使用私有CPU随机流，已有factory核对共同张量未变。SPCG新H按修订版独立seed2026111600，在实施阶段生成并冻结字节，本轮未生成。

G0应直接使用该未训练LQI构造结果，不调用SCQ/RF/RIVE factory，不加载已训练权重，也不以SCQ/RF的residual初始化bin充当完整母版。母版的“未训练身份”在本轮确认为源码、配置与构造次序；真实新模型的共同初态fingerprint要在后续获授权CPU／CUDA阶段生成核验，本轮没有实测模型参数指纹。

现有静态配置仍含旧`attn`字段，它们用于先构造legacy，再由factory替换全局分支；不能单凭字段名认定仍执行Transformer Attention，也不能静默删掉构造所需字段。局部DynamicGraph模块按既有母版保留。

## 4. 首次coarse插入点及必要的最小改动

已绑定的`models/AdaPoinTr.py`中，`PCTransformer.forward`先由`encode_rim_proxy_tokens(xyz)`获得coor／x，再在1728–1731行生成z和learned_coarse。正确替换点是原`self.coarse_pred(global_feature)`，其之前已具备S=coor、F=x、z=global_feature及当前D输入。mem_link为Identity的母版约束已在LQI factory显式要求，故F与送入decoder的Memory同宽、同索引；不是另外取一套8192点充作Memory。

**仅把coarse_pred替换为接收z的普通Sequential并不够：SPCG还需要D、S、F。** 最小实现应在隔离版本提供显式D/S/F/z调用，G0走原分支，G1/G2直接生成Q；不能先算旧Q0再残差修正。须保持训练／eval两条消费路径一致，避免hook只捕获detach后的诊断张量，或跨forward残留context。

Q继续传至mlp_query、LQI的q_pos／邻域、坐标排序与逆排序、FC中心、返回coarse及coarse loss。dense仍是coarse中心加FC相对坐标，每中心32点，总8192。现有forward即使learned_only也有继承的输入FPS计算；不能以本轮名义顺带删除或改变其它路径。

最小实现须用人工路径验证确认S/F对齐、Q梯度与实际消费者贯通，并确认旧coarse head未继续注册到G1/G2 optimizer；这属于后续实施验证，不是S0已完成的运行结论。

## 5. 实际loss和数值合同

`AdaPoinTr.get_loss`返回去噪项和reconstruction；在denoise_weight=0时首项为0，reconstruction仍是CD(coarse256,GT8192)+fine loss。fine_coverage_weight=1、fine_local_weight=0时为原双向L1 Chamfer；runtime把两个返回项相加后做一次backward。不存在“loss_sparse为0所以没有coarse监督”的情况。

继承源码的Chamfer PyTorch分支用cdist平方→方向最小值→sqrt→两向均值半和。已有helper明确拒绝compiled Chamfer，故后续必须保持FP32 cdist合同，不能自动换后端。S0只核对文本与既有后端合同，没有重新导入Chamfer或实测CUDA路径；本轮20项之外的整个扩展二进制未重新全量哈希。

监督仅在loss入口读取G；coarse/head/forward只接D及D-derived条件。不新增H1/H2、rim、排斥、厚度、位置loss，不改变默认FC重建。训练固定AdamW和no-decay分组、clip10、LR与BN调度及已有有限Mamba梯度非确定性披露。

## 6. 数据与完整批次顺序

本机读取的manifest、fold和两份order与本次服务器SHA一致，已重新做纯文本／JSON语义核对：420唯一病例、84来源各五种缺损；8k输入／8k目标、defective_bbox归一化；每折63train／21dev来源，315／105病例。train交集42来源，dev互斥；每折dev在另一折train内，不能作为独立双重复。

| 折 | order文件原始SHA256 | 更新／曝光／drop |
|---|---|---|
| C | `{info['C']['order_sha256']}` | 3900／31200／300 |
| D | `{info['D']['order_sha256']}` | 3900／31200／300 |

逐epoch核对100遍×39个8例batch，每遍312曝光＋3drop，完整无重复分割315train病例；正式三臂复用同折order原始字节，不重新抽样“相同seed”。

实际训练根为`data/bcsp_geov1_foldc_8192_seed0_v1/points`和`data/bcsp_geov1_foldd_8192_seed0_v1/points`。各315个指定NPZ均为非空普通文件，父路径无链接；630是两个根的文件数，表示420种病例及部分重复副本，不是630独立病例。开发输入可按既有冻结映射使用另一折训练根，本轮不复制新数据。

本轮未重新读取或哈希NPZ内容，不能把存在性检查写成新一次payload几何QC。继承已冻结QC，正式执行前只在明确范围内重验实际使用输入。

## 7. 已收敛的实施范围与剩余事项

下一轮若获implementation-only授权，可集中完成：①隔离SPCG head／固定U；②母版factory及显式D/S/F/z的最小coarse接入；③短入口／runtime日志与1GiB输出计数适配；④一批人工CPU回归与P3。保留现有provider、数据、训练生命周期和评分器，不新增通用库存、传输或PID框架。

必须在实施中核清的新候选内容：H/U真实字节、G1/G2等参数及共同初始化、两个forward分支的消费者、总loss Q梯度、不把FPS索引当可导、固定数组并列排序、G1解析简化数值差异、无GT入口与1GiB输出估算。它们尚未实现或测试，不能当作S0缺陷继续逐项服务器试跑。

实施／CPU/P3通过后才创建修订版既定CUDA的待授权范围：6人工＋5训练D-only＝11forward／3loss／3backward／0step；不恢复旧RIVE训练模型，不自动训练。后续每次执行仍遵守用户确认的分阶段边界。

## 8. 证据与权限

本目录保留调用范围、20项大小／哈希、远端原始stdout／stderr与命令长度、630条文件属性、完整order语义结果及本报告。read-only审阅不是CPU contract tests，也不是CUDA／科研效果证据。所有新增文件均在本机S0证据目录，生产代码和服务器文件保持不变。
'''
(O/'BCSP_SPCG_S0有限只读差量核对报告_zh_v1.md').write_text(report,encoding='utf-8')
save('S0_completion_v1.json',dict(status='S0_REVIEW_COMPLETE_READY_TO_DEFINE_IMPLEMENTATION_ONLY',critical_readonly_checks=checks,remote_scope_sha256=sha(O/'S0_readonly_scope_v1.json'),remote_result_sha256=sha(O/'S0_remote_result_v1.json'),report_sha256=sha(O/'BCSP_SPCG_S0有限只读差量核对报告_zh_v1.md'),implementation_authorized_by_this_receipt=False,CPU_tests_run=0,GPU_calls=0,training=0,NPZ_payload_reads=0,checkpoint_loads=0,server_writes=0))
print(json.dumps(dict(status='S0_REVIEW_COMPLETE_READY_TO_DEFINE_IMPLEMENTATION_ONLY',all_checks=all(checks.values()),folds=info,available_GiB=storage['current_available_GiB']),ensure_ascii=False))
