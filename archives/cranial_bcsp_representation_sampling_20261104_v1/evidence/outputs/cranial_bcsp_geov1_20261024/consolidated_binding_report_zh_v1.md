# 母版、proxy几何与新训练合同合并绑定报告

_2026-10-24 · 本机限定CPU几何＋文本／元数据核对 · 不运行模型、不操作服务器_

## 📋 结论与完成状态

完成一个合并核对包：选择本机冻结归档作为新实现父版；固定六例上完成8k/16k两级FPS几何模拟；锁定不改变batch的KNN资源策略；从历史元数据重建C/D分区并核对两份历史训练名单哈希；形成最多四run的新任务设计合同。

状态为 **DESIGN_BOUND_NOT_EXECUTION_READY**。没有创建训练request。新数据尚未生成、实现适配尚未进行、CUDA资源尚未验证，不能宣布可直接训练。

## 📦 母版选择

采用本机 `outputs/cranial_scqr_v12_qa_github_publish_20261019` 冻结归档作为父版，而不使用漂移的work副本或混拼旧hotfix。选择依据是已有归档身份可追溯，不是认定它等同当前服务器安装。

选定模型SHA256：`1f3eb07ad0c3e2f78756682dcb273d745939dc7efda5563c6528915d6d89a1d4`。

模型、Transformer_utils、PointNet2适配器、misc、runner、builder、Dataset七个关键父文件及哈希见[mother_and_training_design_binding_v1.json](E:/Codex/2026-06-06/mamba-ccf-c-1-high-resolution/outputs/cranial_bcsp_geov1_20261024/consolidated_binding_v1/mother_and_training_design_binding_v1.json)。这是关键修改父版清单，不冒充全部依赖锁。未复制或修改七个父文件。

新任务保留B0关闭Local/SCF/Query附加机制的模型语义，中心[512,256]、query256、FC输出8192；旧训练stage和3939-step守卫不得复用。新stage、100遍计数和输入schema适配仍需一次限定实现。

## 📊 限定proxy几何检查

一次顺序CPU计算，退出码0，主体29.312秒；六例、每例V1输入8192/16384、仅sampling seed0。读取同六例D/G重建真实J，不访问其他病例payload。12个NRRD与12个既有派生NPZ前后SHA256相符且历史绑定匹配。

NumPy float64 FPS固定首点0、并列取首索引，模拟N→512→256；512中心向原始输入做k=16近邻，另统计邻域并集。它不是实际PointNet2 CUDA执行，不证明其浮点／并列点取序相同，也不读取神经网络特征。原输入和代理坐标均以世界mm评价。

下表是六例等权平均；P95是病例P95的均值，不是汇总所有面后的P95：

| 阶段 | 8k：J覆盖@1mm | 16k：J覆盖@1mm | 8k／16k：J-P95 mm |
|---|---:|---:|---:|
| 原始输入 | 15.83% | 28.59% | 4.020／2.979 |
| 第一层512中心 | 1.56% | 1.35% | 8.845／8.690 |
| 最终256代理坐标 | 1.03% | 0.89% | 11.473／11.381 |
| 512中心直接原始近邻并集 | 14.13% | 18.04% | 4.316／4.579 |

原输入靠近J的点中，落入上述直接邻域并集的比例，六例平均从89.51%降为63.44%。这不是“丢失了36.56%的学习信息”：第一层原始点图特征已包含邻域信息，尚有两跳及其他通道；本表只说明可追踪的直接几何支持。

**解释**：输入16k有明确几何增量，固定中心预算没有转化为更密的proxy坐标覆盖；直接邻域支持仍增加，但其尾部P95并非同步改善。不能说16k完全无用，也不能保证它改善模型。低proxy坐标覆盖不是失败门，因为proxy表达的是邻域特征而非完整表面采样。

本次与上一包三seed平均不同，原因是这里只取seed0，并非指标漂移。当前没有全局内外板语义、学习特征保留率或完整生产P3结论。

## ⚙️ KNN资源策略

选择**query分块、全key精确搜索**的最小适配策略：固定query chunk=256，保留全部16k key，不采用近似搜索，不先降回8k。B=8、FP32时单个距离块约128MiB，相比全16k×16k矩阵8GiB大幅降低该项存储。

128MiB不是总显存承诺：其他激活、topk、输出、优化器和并发临时张量仍须核验。仅决定策略，本轮未改代码、未实现KNN、未测GPU。

下一限定实现必须同时作用于两臂，保留原距离公式、k、self-neighbor及索引语义；CPU回归覆盖随机、重复、等距、空／非法shape、边界chunk，并明确并列邻居是否仅允许合法集合等价。浮点近邻边界和CUDA实际一致性仍需单独核验，不能先写“完全等价”。

保持共同global batch=8与step_per_update=1，不用自动减microbatch＋累积来绕过资源风险。后者会改变BN与梯度合同。若分块策略仍不能满足资源，停止并报告，不自动换方案或加proxy。

## 📚 Source/fold与更新数绑定

只读SkullBreakPC manifest元数据，采用已有 `mamba-v12-mechanism-development-v1-20260805` 稳定分配算法：104个strict-train源中排除20个confirmation，余84源分A–D；未打开confirmation／monitor／official-test的点云或原始payload。

复用C/D开发折，而不是另造结果导向split：

| 项目 | Fold C | Fold D |
|---|---:|---:|
| train source／case | 63／315 | 63／315 |
| dev source／case | 21／105 | 21／105 |
| 每遍batch，drop_last | 39 | 39 |
| 精确遍历数 | 100 | 100 |
| optimizer updates | 3900 | 3900 |
| case曝光次数 | 31200 | 31200 |

训练名单文本SHA256与历史request双双相符：

- C：`3c5883d1f582b90533ffed3ae61b1bbe8b88c39b75f40faddf25b63d8f93836d`
- D：`682067ea877e8370e5c3d0ac7b2cdd7ae3b2b372a146829b42491899aa1c0aa1`

C/D的dev源互斥，但train集合按交叉验证设计重叠；不能称两个独立训练总体。每遍剩余3case不进入batch，顺序与逐源曝光必须保存，不假设100遍人人恰好等次数。

[fold_binding.json](E:/Codex/2026-06-06/mamba-ccf-c-1-high-resolution/outputs/cranial_bcsp_geov1_20261024/consolidated_binding_v1/fold_binding.json)保存精确source和case ID。元数据manifest哈希为`6a6b5aa3ba4e09758bd0f74a59b0f26f8edeac77614f45d522e65c2d98dc776e`；它是当前基础PC metadata，不等于旧out8192 manifest或未来新BCSP manifest。

上述3900是固定名单**全部几何QC通过且每源五缺损均保留**时的设计绑定。新数据生成／QC未完成，不假装训练资产存在；若失败source导致M改变，不静默删源后仍宣称3900合同成立，必须形成新版本。

## 🎯 四run范围与下一步

明确采用的设计是：V1完整边界面积采样8k→8k与16k→8k，Fold C/D，seed0，共四run上限。V1是共同几何定义而非已胜出的采样法；比较回答点数收益，不能解释成V1优于V0。

共同条件：同一目标坐标、D-only归一化、source split、初始化seed、数据顺序、AdamW lr1e-4／decay5e-4、bias/一维参数不衰减、clip10、FP32、确定性／TF32关闭、query256／FC factor32、中心[512,256]、100遍标签0–99、final-only、scratch。不自动BNCal或评价，不改变输出16k或proxy1024。

这是训练设计绑定，不是冻结执行request：仍欠新派生数据全量QC／哈希、共同目标及顺序文件、独立新stage守卫、限定KNN适配验证及必要GPU零更新／资源核验。不能从CPU几何代理通过自动推导GPU训练授权。

下一步建议一个集中implementation-only包：在选定父版之外新增候选适配，完成query分块KNN与新任务数据／计数接口的针对性CPU验证；不部署、不构建环境、不运行真实模型或创建训练request。新数据生成也须精确限定到上述开发源，不能视本轮metadata绑定为payload读取授权。

## 🔐 范围与复核

仅新增当前outputs下的probe、几何指标、绑定与报告。旧源数据、生产源码和历史报告不改。无torch导入、无模型／checkpoint、无GPU、无服务器、无训练request；没有下载或安装依赖。CPU FPS是专用几何分析，不是通用审计框架。

科学文档技能用于明确区分源码事实、CPU代理、理论内存与未执行范围；报告使用AI辅助实现与分析。完整P3和几何访问隔离测试未因此宣告通过。
