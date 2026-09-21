# 颅骨点云补全 Cranial-SCQR v1.1：Round A-I Q0 反向推理干预实验报告与下一阶段建议

**报告日期：**2026-09-19（UTC）  
**文档性质：**已完成实验的事后报告与下一阶段研究建议；本文本身不是新的训练、数据访问或推理授权。  
**研究背景：**以 AdaPoinTr 为基础，在颅骨缺损点云补全中检验局部几何、接触监督与查询条件化。长期目标是形成具有可验证 Mamba 贡献的论文，而非仅取得某一次开发集分数。  
**本轮范围：**一次经单独授权的 `Q0 weights × inference β=1` 正式反向干预，及其后的只读科学复盘。Round A 开发集评估和 Round A-I QC 同权重干预仅作为已冻结父结果复用。

> **交付与文件系统边界。**本报告在服务器项目 `/home/jovyan/adapointr_work/PoinTr` 内生成。Windows 本机目录 `E:\Codex\2026-06-06\mamba-ccf-c-1-high-resolution` 与服务器不是同一文件系统；本报告没有直接写入、读取或验证该 Windows 目录。本机归档或备份是否完成，必须由研究者下载并核验后确认。报告撰写过程中没有打开 NPZ、反序列化 checkpoint、调用 GPU 或修改任何既有实验产物。

## 1. 摘要与核心结论

正式干预通过全部执行与科学门控：两条 Q0 Fold A/B seed-0 BNCal checkpoint 各加载一次；严格按两折开发清单访问 210 个 case，每 case 依序执行 `native_q0` 与 `q0_beta1`，共 420 次模型 forward。`partial` 是唯一模型输入；`implant`、`gt` 仅用于推理后计算指标。临时 β=1 赋值和精确恢复各 210 次；QC checkpoint 加载、QC forward、优化器构建、训练更新及 BNCal 均为零。模型参数与持久 buffer 在每折前后完全一致，两个 checkpoint 文件的 SHA256 在运行后仍与冻结值相同。正式输出的 `files.sha256` 清单逐项校验通过。

在冻结主指标 `rim_gt_rim_to_pred_p95_mm`（越低越好）上，Q0 同一权重立即把 β 从 0 改为 1 的合并差值为 **+0.000271 mm**，Fold A 为 −0.000288 mm、Fold B 为 +0.000831 mm；合并 95% source-skull cluster-bootstrap 区间为 [−0.000161, +0.000708] mm。它按事先固定的 0.01 mm *实用不活跃*规则分类为 `Q0_REVERSE_EFFECT_INACTIVE`，但这不表示数学上的严格等价或临床无差异。

在相同推理 β 下，Q0 相对独立训练的 QC 权重状态有约 **−0.147 mm** 的平均方向性优势，但两种 β 的置信区间均跨过 0。冻结分析器给出的总体结论 `WEIGHT_STATE_DOMINANT_DIRECTIONAL` 可作为本轮**预设分类**，不可扩大为“已证明 β 的训练路径必然造成优势”“跨训练种子稳健”或“临床有效”。既有 Round A 开发集门控因 QC 未优于 Q0 而为 `NO_GO`；本轮结果没有推翻该门控，也不授权 Round B。

## 2. 科学问题与对照设计

### 2.1 研究问题

Round A 原始结果中，QC 在主指标上弱于 Q0；先前同一 QC checkpoint 下的推理干预显示，β=1 接触偏置的即时空间对齐收益虽在骨骼重采样区间上有方向性证据，点估计却只有约 0.00035 mm。由此出现两个可区分的问题：

1. 对同一组 Q0 权重，推理时临时改用 β=1 是否产生有实际意义的改善？
2. 如果 Q0 与 QC 仍有差距，该差距主要与**独立训练形成的参数及 buffer 状态**相关，还是可由推理时 β 的即时效应解释？

本轮只填补预先冻结的 2×2 设计中缺失的 `Q0 weights × inference β=1` 一格。四格定义如下；QC 两格复用既有冻结结果，绝不重新加载 QC checkpoint：

| 训练后权重状态 | 推理 β=0 | 推理 β=1 |
|---|---|---|
| Q0（训练时 β=0） | 本轮 `native_q0`，并逐 case 对齐冻结 Round A Q0 | 本轮 `q0_beta1`，仅临时改 β buffer |
| QC（训练时 β=1） | 冻结 Round A-I `bias_zero`，在 logits 层实现 β×log(p)=0 的对应条件 | 冻结 Round A-I `native_qc` |

两折 Q0/QC 的运行配置在功能上均启用同一局部几何、接触监督和查询条件化结构；候选名称与 `contact_bias_beta` 分别为 Q0/0、QC/1，另有授权回执等管理字段不同。但 Q0、QC 是各自训练并 BNCal 的 checkpoint；因而“权重状态差异”包含参数、持久 buffer、随机优化路径和可能的训练数值波动，不能从单 seed 结果进一步分解成 β 的唯一训练因果作用。

### 2.2 预设统计与门控

- 主指标：去归一化后以 mm 表示的 `rim_gt_rim_to_pred_p95_mm`；所有距离类差值均为“左−右”，负值代表左侧更好。
- 开发集：Fold A 与 Fold B 各 105 case、21 个来源骨骼；每个来源骨骼 5 种缺损，共 210 case、42 个来源骨骼。统计单位不是 210 个相互独立的病人。
- 置信区间：每来源骨骼先等权平均其 5 个缺损，再在两折各 21 个来源骨骼内独立重采样；两折合并等权；预设随机种子 20260910、10,000 次 percentile bootstrap、双侧 95% 区间。此区间条件于现有 seed-0 训练结果，**不**覆盖训练种子方差。
- Q0 原生复现门：每 case 的距离指标最大绝对误差 ≤1e−5 mm、单位区间指标 ≤1e−8，整数与布尔字段完全相同。
- coarse 不变门：条件之间最大绝对差 ≤1e−7（归一化坐标）。β buffer 精确恢复、模型全部参数和 buffer 哈希不变。
- 即时效应“实用不活跃”门：Q0 β1−β0 主指标在 Fold A、Fold B 及合并值的绝对值各 ≤0.01 mm。这个数值继承自先前冻结 Round A-I 协议，**不是**临床专家给出的可接受误差，更不是以后新模型选择的通用阈值。
- 二级护栏同时记录 implant/final CD-L1、final HD95、final NSD@1 mm、灾难 case 与接触相关指标；不得仅以主指标筛选有利叙事。

## 3. 数据、资源、实施和完整性

### 3.1 父结果与输入边界

| 角色 | 固定来源及用途 |
|---|---|
| Q0 Fold A/B BNCal checkpoint | 各加载一次；其训练为 seed 0、各自 315 个训练 case、AdamW、FP32、batch 8、101 遍历、3939 optimizer steps；训练成功后各有一次 315-case、40-batch、partial-only BNCal。这些训练和 BNCal **不是本轮重新执行**。 |
| Fold A/B development 清单 | 各 105 case，互不重叠；本轮共打开 210 个对应 NPZ。 |
| Round A 开发集冻结指标 | 用于核对本轮 `native_q0` 的逐 case 复现，不加载该轮的其他 checkpoint。 |
| Round A-I protocol-v2/run1 冻结指标 | 仅复用 QC 的 `native_qc` 和 `bias_zero` 两格；QC checkpoint 加载和 QC forward 均为零。 |

本轮没有读取 confirmation20、official test、old monitor、MUG 或清单外训练 payload；没有保存预测点云或原始张量。数据目录属于服务器 `/home/jovyan/datasets/SkullBreakPC_out8192`，与任何 Windows 路径无自动同步关系。

### 3.2 执行环境与审计计数

2026-09-19 06:13–06:17 UTC，单张 NVIDIA GeForce RTX 4090 D（UUID `GPU-3f28fa66-923a-0815-6594-075e89429bf9`）、`CUDA_VISIBLE_DEVICES=0`、Conda Python 3.10.20、PyTorch 2.4.1+cu118、CUDA 11.8、FP32、eval、无梯度、batch 1、`num_workers=0`、固定 Fold A→B 及清单 case 顺序。单次 tmux launcher 退出码 0；主日志、授权回执及新正式输出目录均按 v2 请求固定。

| 计数或检查 | 实测 |
|---|---:|
| Q0 checkpoint 加载 / QC checkpoint 加载 | 2 / 0 |
| NPZ 打开、`partial`、`implant`、`gt` 读取 | 各 210 |
| Q0 条件 forward | 420 = 210×2 |
| β 临时赋值 / 精确恢复 | 210 / 210 |
| QC forward、优化器构建、optimizer step、参数更新、持久 buffer 更新 | 全部 0 |
| Q0 逐 case 原生复现最大距离/单位区间误差 | 0 / 0 |
| coarse 条件间最大归一化差 | 0 |
| 参数与 buffer 前后哈希 | 两折均不变 |

此次输出包含 420 行条件级指标、168 行来源骨骼×条件汇总、420 行诊断、168 行配对差值、机器可读汇总及结论回执。输出目录内 10 个 payload 文件全部通过 `sha256sum -c files.sha256`；Round A 与 QC 干预两套父结果也分别通过其冻结清单。`files.sha256` 文件本身 SHA256 为 `a6e68218221623960e5103b3312495d59458b7e34b7bfd14f7f0c6de2aed4d2b`。正式主日志在结果目录外，不能把“清单通过”误写成已验证日志或本机备份。

## 4. 正式结果

### 4.1 四格主指标与冻结对比

| 权重状态 × 推理 β | Fold A | Fold B | 两折等权合并，mm |
|---|---:|---:|---:|
| Q0 × β0 | 8.580731 | 7.709525 | 8.145128 |
| Q0 × β1 | 8.580443 | 7.710356 | 8.145400 |
| QC × β0 | 8.684004 | 7.901812 | 8.292908 |
| QC × β1 | 8.684074 | 7.901043 | 8.292559 |

| 冻结对比（左−右；负值较好） | Fold A | Fold B | 合并点估计 | 来源骨骼 bootstrap 95% CI，mm |
|---|---:|---:|---:|---:|
| Q0 β1 − Q0 β0：同权重即时 β 效应 | −0.000288 | +0.000831 | +0.000271 | [−0.000161, +0.000708] |
| Q0 β0 − QC β0：β0 下权重状态对比 | −0.103273 | −0.192286 | −0.147780 | [−0.476911, +0.182370] |
| Q0 β1 − QC β1：β1 下权重状态对比 | −0.103631 | −0.190687 | −0.147159 | [−0.476144, +0.182913] |
| 交互：(Q0 β1−β0)−(QC β1−β0) | −0.000358 | +0.001599 | +0.000621 | [+0.000160, +0.001095] |

先前 QC 同权重结果中，`bias_zero − native_qc` 合并为 **+0.000350 mm**、95% CI [+0.000210,+0.000493] mm；因此 QC 权重下将 β0 改 β1 的方向是约 −0.000350 mm，虽有统计方向性证据，幅度仍远低于 0.01 mm。Q0 权重下即时改 β 的合并方向反而略差。交互区间未跨 0，但其约 0.000621 mm 的绝对大小、两折异向和协议中的“仅描述性诊断”角色，均不支持将其包装为实用创新收益。

### 4.2 次要指标和来源骨骼异质性

Q0 β1−β0 的合并 implant CD-L1 为 +0.0000476 mm、final CD-L1 为 −0.00000521 mm、final HD95 为 −0.00001696 mm、final NSD@1 mm 为 +0.00000271。这些差异的量级均很小，部分指标的区间不跨 0 并不自动意味着实际价值；不能在多个指标间挑选最有利者作为新主张。

在 42 个来源骨骼上，Q0 β1−β0 主指标有 17 个负、25 个正，范围约 [−0.002802,+0.003662] mm；β1 下 Q0−QC 权重状态对比有 25 个负、17 个正，范围约 [−2.498,+2.365] mm。后者的来源骨骼异质性远大于其 −0.147 mm 合并均值，解释了置信区间为何跨 0。两折 Q0 即时 β 效应方向相反，也提示不能只报合并值。

### 4.3 与 Round A 门控及既有负对照的关系

冻结 Round A 开发集评估中，Q0、QC 相对 B0 的合并主指标分别约为 −3.681、−3.534 mm；然而 `QC−Q0=+0.147430 mm`，不满足预设的接触偏置增量必须 `<0` 条件，因此 Round A 总门控为 `NO_GO`，`round_b_authorized=false`。本轮的 Q0 反向补格没有提供推翻这一事先决策的新证据。若要以 Q0 为新候选，必须建立**新的独立研究问题与授权链**，不能把原 QC Round B 改名后继续。

Round A-I protocol-v2 的 `case_mean_probability` 对 `bias_zero` 在 attention 层满足 ≤1e−6 负对照门，实际最大误差约 1.86e−9；但其下游距离/接触指标仍有数值敏感性，主指标的合并负对照差约 +0.00000236 mm。故本轮 0.000271 mm 即时效应不能武断称作“全是浮点噪声”，同样不能因非零就声称有实用研究收益；应区分 attention/logits 层机制、预测坐标、离散近邻指标和实际问题价值。

## 5. 可靠性、因果解释与论文表述边界

1. **内部有效性较强，但范围有限。**固定 checkpoint 内的 β 干预是受控的：输入 case、模型权重、执行模式和指标保持一致；原生 Q0 精确复现、coarse 不变、β 完全恢复及全模型状态不变均通过。这支持“在这两条已训练的 Q0 模型中，推理 β=1 的即时主指标效应按预设规则实用不活跃”。
2. **权重状态关联不是训练机制唯一因果证明。**Q0 与 QC 虽在主要功能配置上以 β 为关键差异，但分别训练并 BNCal，且目前只有每折 seed 0。跨 checkpoint 差异可能混有训练随机性、优化轨迹及持久 buffer 差异。不能写成“β=1 在训练中必然伤害性能”或“Q0 必然优于 QC”。
3. **骨骼重采样区间不能替代训练种子区间。**42 个来源骨骼而非 210 个独立病人是更合适的当前重采样单位；不过 10,000 次 bootstrap 仅描述这批开发集来源骨骼在当前 seed-0 模型下的不确定性，不包含不同训练随机初始化和数据顺序的方差，也不是外部人群推广保证。
4. **统计方向与实际意义要分开。**QC 即时收益和交互可以出现不跨 0 的来源骨骼区间，同时仍远小于协议内 0.01 mm 的探索性实用阈值。该阈值缺少临床锚点，不能称为“临床可接受”或“临床无意义”的正式界线。医工问题的指标及容差应由任务需求和专家判断前置确定，而不是照搬模型损失或观察到的改善量。
5. **开发集选择偏倚。**B0/A1/Q0/QC 与后续机制对比都已在同一 development84 框架下观察；本轮探索性 `Q0−A1` 对照不可事后冒充预注册门槛。confirmation20 与 official test 仍须封存，直到候选、主指标、护栏和一次性评估方案全部冻结。
6. **研究定位限制。**Q0 与 QC 的现有配置均为 `mamba_adapter.enabled=false`。本轮最多支持 Cranial-SCQR/query-conditioning 的实验机制叙述；不能用于证明“Mamba 改进了颅骨点云补全”。

适宜写法：**“在固定 seed-0 的开发集模型中，β 的即时推理效应按预设阈值实用不活跃；Q0 相对 QC 的权重状态优势呈方向性但未达到稳健统计证据，且存在显著来源骨骼异质性。”** 不宜写“已经证明权重状态主导改善”“β 完全无效”“临床显著改善”或“已验证 Mamba 机制”。

## 6. 截至 2026-09-19 的定向文献核验与研究定位

以下是与本轮判断和下一阶段设计直接相关的**定向**原始论文核验，不是穷尽式系统综述；预印本状态与论文主张不得混同为本项目已验证事实。

| 文献 | 已核实的相关点 | 对本项目的含义 |
|---|---|---|
| [AdaPoinTr，Yu 等，2023](https://arxiv.org/abs/2301.04545) | 自适应查询生成和去噪任务构成基线核心。 | 必须保持基线实现与问题定义可追溯；本项目新模块要有相对 AdaPoinTr 的受控消融。 |
| [CompletionMamba，Fu 等，IEEE TIP 2025](https://research-repository.uwa.edu.au/en/publications/completionmamba-taming-state-space-model-for-point-cloud-completi/) | 已研究无序点云的序列化、局部 SSM 与形状感知 Mamba 来完成点云。 | “把 Mamba 放进补全网络”已不是新颖点；若做颅骨方法，需阐明不同的解剖约束与可检验机制。 |
| [3DMambaComplete，Li 等，2024；2026 修订预印本](https://arxiv.org/abs/2404.07106) | 已用 Mamba 建模点云补全并重视高保真局部结构。 | 不宜以一般的 Mamba 编码器替换或局部细节口号作为独立贡献。 |
| [DAPointMamba，Li 等，AAAI 2026](https://ojs.aaai.org/index.php/AAAI/article/view/37596) | 指出直接把 3D 点云序列化为 1D 会损害空间拓扑，并设计几何对应扫描与空间 SSM。 | 若提出边缘/颅骨几何感知扫描，应明确它解决的特殊缺损机制，并与已有空间扫描方案比较。 |
| [PPC-MT，Li 等，2026 预印本](https://arxiv.org/abs/2603.00870) | 已报告 Mamba–Transformer 混合、PCA 引导排序与并行补全。 | 简单串接 Mamba 和 Transformer 也不宜作为唯一创新；须提供参数量、FLOPs、实测延时与质量的公平对照。 |
| [Neural shape completion for personalized Maxillofacial surgery，Scientific Reports 2024](https://www.nature.com/articles/s41598-024-68084-5) | 原始颅颌面点云补全研究强调按缺损区域、去归一化物理单位评估。 | 本项目应继续保留 mm 单位、缺损/边缘指标，同时说明数据生成与目标人群差异；不能直接横比不同数据集绝对分数。 |
| [Metrics Reloaded，Nature Methods 2024](https://www.nature.com/articles/s41592-023-02151-z) | 倡导依问题用途选择互补指标，警惕只用便利指标替代实际目标。该框架针对医学图像任务，不能直接当作点云指标处方。 | 主指标及边界、形状、灾难 case 护栏需有任务理由和预先冻结的解释。 |
| [Accounting for Variance in Machine Learning Benchmarks，MLSys 2021](https://proceedings.mlsys.org/paper_files/paper/2021/file/0184b0cd3cfb185989f858a1d9f5c1eb-Paper.pdf) | 原始方法学研究分析初始化、数据与训练流程等变异来源对算法比较的影响。 | 单训练 seed 的骨骼层 CI 不能直接升级为跨训练的模型优越性结论。 |

这些文献提供的是研究定位和方法学警示，并不意味着某个尚未实现的“边缘感知 Mamba”设计已被证明新颖。正式立项前还需查重其具体算子、序列化、边缘监督与对照设置，并与导师/领域专家讨论临床或工程意义阈值。

## 7. 下一阶段建议：阶段门控而非自动续跑

### P5：无 GPU 的研究问题与方案冻结——当前最优先

推荐**停止 QC/β=1 接触偏置的原定 Round B**，把 QC 留作负结果和机制消融。先只读梳理既有 Mamba 尝试、Q0 相对 A1/B0 的真实增益与护栏、失败 case 的缺损类型及来源骨骼异质性，再决定论文究竟是（甲）非 Mamba 的 Cranial-SCQR 方法，还是（乙）确有 Mamba 特有作用的颅骨点云补全方法。此选择改变下一轮对照组和计算预算，不能由本轮数值自动决定。

从现有冻结 Round A 表探索性计算，Q0−A1 的 rim P95 在 Fold A/B 分别约 −0.564/−0.793 mm，合并约 −0.678 mm；42 个来源骨骼中 29 个偏向 Q0。但 Fold B 的 implant CD-L1、final CD-L1、final HD95 等部分均值略差。因此 Q0 是**值得复核的候选**，不是已通过新的模型晋级门槛。若拟将其作为论文核心，先另行制定独立于本轮观测的实用改善幅度、必要护栏、失败 case 规则和多 seed 统计计划。

### P6：若坚持 Mamba 主题，先提出可证伪的机制而非直接训练

候选方向可作为**待查新假说**：仅从 `partial` 推断可靠的边缘/局部几何线索，用这些线索约束状态空间扫描顺序或局部—全局信息传播，目标是降低边缘 P95 和尾部灾难风险。不得在推理输入中使用 `implant`、`gt` 或任何由完整目标推得的真实 rim；否则产生数据泄漏。设计需回答：为何状态空间建模比现有 Q0 查询条件化更适合该缺损；排序如何保持 3D 邻接；与 CompletionMamba、DAPointMamba、PPC-MT 的具体差别是什么；机制失效时预期诊断是什么。

在下一份独立方案里，应预设至少三个对照：冻结 Q0 无 Mamba、参数/计算量匹配的非 Mamba 容量对照、Mamba-on 候选；若主张“解剖排序”而非 Mamba 本体，还需同参数的普通排序/随机排序负对照。先申请实现-only、synthetic CPU 契约、零更新 preflight 和资源 benchmark 的分别授权；任何一步通过都不自动授权训练。

### P7：仅在方案通过后进行配对训练与开发集评估

若目标是复核 Q0 模块本身，可预先注册 A1/Q0 的同 fold、同新 seed 配对训练；若目标是 Mamba 增量，应优先设计 Q0/Mamba-on/容量对照的配对实验。建议完整计划覆盖 Fold A/B 和至少两个**新**训练 seed，以便与已有 seed 0 合并描述训练方差；实际运行数、预算、停止规则和每次 BNCal 均须在执行前冻结，逐 run 单独授权。这里的 seed 数是计划建议，不是已经授权或已经达到统计稳健性的保证。

开发集主指标继续使用预注册的 mm 级边缘 P95，但未来模型晋级的最小实用改善幅度必须另有工程/临床依据，不能沿用本轮针对 β 即时效应的 0.01 mm 阈值。护栏至少包含 implant/final CD-L1、final HD95、final NSD@1 mm、零接触/灾难 case、各缺损类型与来源骨骼尾部；同时报告参数、FLOPs、峰值显存和同步后的实际推理延时。模型间按来源骨骼配对并分折报告，训练 seed 与来源骨骼两层不确定性应区分；禁止因 seed、fold 或某个指标不利而选择性舍弃。

### P8：封存集与论文结论

只有在开发集上按**新冻结协议**完成候选选择，且没有损害预设护栏后，才单独申请一次 confirmation20 评估；之后再根据其预设规则决定是否申请 official test。两者都不能被用于继续调阈值、调 β 或迭代模型。若新 Mamba 候选不能稳定优于 Q0，应保留负结果、回到研究问题而不是追加未计划的重跑。若最终论文仍以 Mamba 为题，必须有可复核的 Mamba-on/off 增量；现有 Q0/QC 结果不能代替它。

## 8. 证据路径、SHA256 与复核说明

以下路径均相对服务器项目根 `/home/jovyan/adapointr_work/PoinTr`；它们**不是**本机 Windows 路径。正式结果目录创建后未因本报告而修改。

| 证据 | 服务器相对路径 / SHA256 |
|---|---|
| 冻结 Q0 反向干预协议 | `docs/cranial_scqr_v1_research_2026_09_10/l4_round_a_q0_reverse_inference_intervention_protocol_v1.json` / `bf447b2585aa799f00bd0f942033971a567eb2ebc527a6ef3d28664facfd3de0` |
| v2 执行请求 | `docs/cranial_scqr_v1_research_2026_09_10/l4_round_a_q0_reverse_inference_intervention_execution_authorization_request_v2.json` / `505264de56463ecdaa5e931d3a4c7c8ab6d5a8f356e8dd6964a77a31a1281cbe` |
| v2 有效授权回执 | `docs/cranial_scqr_v1_research_2026_09_10/l4_round_a_q0_reverse_inference_intervention_execution_authorization_receipt_v2.json` / `e73b49c9251ad9b956090ce6ecdf57e7352c32cb66ab0d3ccddd90c6d8edb7d8` |
| 本轮正式结果目录 | `logs/cranial_scqr_v11/l4_round_a_q0_reverse_intervention/cranial_scqr_v11_l4_round_a_q0_reverse_intervention_v2_20260919T055847Z/` |
| 正式结果清单 | 上述目录下 `files.sha256` / `a6e68218221623960e5103b3312495d59458b7e34b7bfd14f7f0c6de2aed4d2b`；清单内 10/10 文件校验通过。 |
| 运行回执与主指标汇总 | 结果目录内 `reverse_intervention_execution_receipt.json` / `1f6063a3962fe24b50e2330abca8f1f28c5c89809fde2af01e4e354d3cc40ef5`；`factorial_summary.json` / `8e2eba7bd8047a0067487de5835fb44476e6c3a654a5dd9d923017c703546de2`。 |
| 科学分类回执 | 结果目录内 `weight_state_classification_receipt.json` / `f5a091b56b64ddc13aa28f267176c678bd73ee07e631c78c64674feb7ffcea85`。 |
| Round A / Round A-I 冻结父结果 | Round A `files.sha256` / `a203a4b3a9d9b154f0f22c1e967b407125f26903d22d348f27a7cd415a33df52`；QC intervention `files.sha256` / `7465fc83a530d9fb08c928c1accefa60b65bfd3c367720456a8cdbf5599515f7`。两套父清单分别 16/16 通过。 |
| Fold A/B Q0 BNCal checkpoint | `267572474120963183a2e3ca9651cc2ea1f94b24937748cb67ca426ef92cc75f` / `edd496c3dc7e4cf894e95697bf89e965de353dc38d5173ca665d906f182e5b08`；仅为前后文件哈希记录，本报告未反序列化。 |

**本机交付建议：**由研究者将本报告文件下载到 `E:\Codex\2026-06-06\mamba-ccf-c-1-high-resolution\` 的同名文件中，再对下载文件独立计算 SHA256，与服务器生成后的交付哈希比对。只有完成该操作并由研究者明确确认后，才可称本机已有这份报告。长期归档目录 `E:\ResearchBackups\AdaPoinTr` 的状态同理不可从本远程任务推断。本文没有打包、传输、删除或清理任何服务器实验产物。
