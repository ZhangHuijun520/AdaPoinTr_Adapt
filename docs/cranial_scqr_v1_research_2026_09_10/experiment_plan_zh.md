# 颅骨点云补全下一阶段正式实验计划

## 1. 研究目标与计划状态

本计划以 AdaPoinTr implant 表面点云补全为基线，优先验证 **partial-only soft contact-support conditioning 是否具有独立于额外网络容量的补全收益**。工作代号为 `cranial-scqr-v1.1`。文献与代码审查截止 2026-09-10，修订依据见同目录 `review_zh.md`。

这是供后续实施的正式研究设计，不是实验执行授权。P0 的数据身份、实现契约和预算锁定完成前，状态为 `DESIGN_READY / EXECUTION_LOCK_PENDING`。本文件不授权修改模型、读取数据 payload、启动 preflight、性能计时、训练、归档或删除。当前交付仅包括研究文档。

目标限定为几何重建研究。不预设 CCF C 录用，不声称临床安全，不要求为维护“Mamba 方向”而保留无效模块。若 Mamba 没有净收益，论文应以得到证据的接触机制或其他实际有效机制组织。

## 2. 科学假设与最小对照

### 2.1 假设

H1：从 defective 点云可以预测 proxy 邻域的接触支持分数；其开发集识别表现优于无信息的类别先验参考。

H2：在额外局部特征、辅助监督和 query-attention 容量相同的条件下，接触偏置可以降低 RimCover-P95，且不造成 implant/final 的明显退化。

H3（条件性）：在已成立的 SCQR 上，Mamba 相对同预算 Transformer 有独立质量增益或质量—效率优势。

H4（后续独立设计）：可见供体与对称可靠性能够帮助某些缺损，但必须避免在跨中线、双侧和不对称病例中强行使用错误先验。

H1、H2 是当前核心；H3、H4 不是已经证实的前提。D2/D5/D6 仅作为提出假设的历史依据，不用于给新候选记成功。

### 2.2 四个核心模型

| ID | 局部几何残差 | SCF 辅助监督 | 额外 query attention | 接触 log-bias | 回答的问题 |
|---|---|---|---|---|---|
| B0 | 无 | 无 | 无 | 无 | 新训练的匹配 AdaPoinTr |
| A1 | 有 | 有 | 无 | 无 | 局部特征与监督的联合增量 |
| Q0 | 同 A1 | 同 A1 | 有 | β=0 | 普通额外 attention 的增量 |
| QC | 同 A1 | 同 A1 | 与 Q0 完全相同 | β=1 | 接触条件化的独立增量 |

QC−B0 是整套方法增量；QC−Q0 是接触偏置增量；Q0−A1 是额外 query 路径增量。A1−B0 不拆分局部特征和辅助监督，故 A1 不能命名为“SCF only”。

所有模型均从头训练，不使用历史 O0/D2/D3 checkpoint、教师输出或其他可能见过当前评估来源的权重。按 seed 固定公共主干初始化；新增模块使用独立 RNG 流，避免创建模块顺序改变公共层初值。Q0 与 QC 初始参数、辅助监督、数据顺序完全一致，唯一设计差异为 β。

若将来需要分别声称 local 与 auxiliary 有效，补充 `A0=local-only` 四折对照，增加 4 个 run，另行授权；不是首轮必做。

## 3. 数据协议与来源账本

### 3.1 既有数据角色

| 数据角色 | 预期规模 | 允许的研究用途 | 禁止的解释 |
|---|---:|---|---|
| development84 | 84 skull / 420 case | 适应性开发；4 折 OOF | 未接触独立测试 |
| 每一开发折 | 63 train / 21 dev skull | 315 train / 105 dev case | case 随机切分 |
| confirmation20 | 20 skull / 100 case | 审计后决定是否阶段性确认 | 自动称完全未暴露来源 |
| 历史 SkullBreak official | 20 skull / 100 case | 方法冻结后的历史 benchmark | 用于当前结构/阈值选择 |
| 现有 SkullFix 小测试子集 | 以锁定清单为准 | 适用范围明确的补充实验 | 自动等于完整官方 110-case test |
| MUG 及历史 D3–D6 来源 | 以 source ledger 为准 | 仅在另行授权的开发/外部验证阶段 | 不同缺损自动等于独立 skull |

保持既有 84/20 和 A–D 分组，不因新指标或案例难度重新洗牌。任何元数据规模不符，应暂停锁定，不自行补样或删除。

### 3.2 Source-use ledger

在获准读取元数据后建立 `source_use_ledger.csv`，至少包括：规范 source ID、数据集及别名、原始来源标识、派生缺损 IDs、现有 split、训练/BNCal/教师/预训练/可视化/阈值选择/确认使用情况、证据文件与哈希、首次暴露阶段、是否允许当前训练。

去重首先使用来源元数据，不只比较派生 NPZ 文件哈希；跨数据集重采样和重命名可能属于同一 skull。必要的几何近重复检查涉及 payload，须另行明确授权，不能在元数据审计中偷偷扩展。

### 3.3 confirmation20 的决策

既有文件说明它从历史 104-skull strict-train 池中划出，故先标为 `historically_source_exposed`。进一步核对它是否曾被评价、用于手工失败分析，以及母模型/教师是否见过它。

- 若当前模型从头训练、只用 development84，且其结果未影响本阶段设计，可作“历史暴露来源上的阶段性留出确认”。
- 若已被直接用于本阶段选择，不再作为确认终点，只能作为历史开发材料。
- 若需要新来源确认，先锁定新的受试者级来源与获取权限；找不到时应如实声明缺少强独立确认，不伪装成 sealed test。

所有去重与确认资格结论记录为 receipt。未决时允许在授权范围内继续开发，但禁止开启最终确认。改变名字或重新生成缺损不能恢复数据独立性。模型选择对有限开发集的适应性会造成偏差。[^1]

### 3.4 输入与标签边界

模型推理仅接收 `partial` 点云及可由该 defective 输入得到的归一化信息。不得输入 GT implant、complete、GT rim mask、缺损类别真值、GT 确定的 rim-local 裁剪或 GT 对称平面。

训练标签仅由 fold-train 的 GT 构造；dev GT 只进入离线 evaluator 和已授权的 oracle 表示审计，不进入模型 forward、BNCal 或训练损失。GT 无泄漏测试必须覆盖预处理与归一化，而不仅是 forward 参数列表。当前 SkullBreak 预处理代码写明 `defective_surface` 归一化；实际 manifest 仍须核对。

## 4. 评价终点

### 4.1 主终点的精确定义

所有距离先恢复到同一物理世界坐标、单位 mm。记固定 defective 表面样本为 D、GT implant 为 G、预测 implant 为 P，定义：

\[
R_G=\{x\in D:\min_{g\in G}\|x-g\|_2\le2\text{ mm}\},\quad
R_P=\{x\in D:\min_{p\in P}\|x-p\|_2\le2\text{ mm}\}.
\]

\[
\operatorname{RimCoverP95}(P)=Q_{0.95}\{\min_{p\in P}\|r-p\|_2:r\in R_G\}.
\]

复用 `utils/skullfix_metrics.py::point_rim_metrics` 的 `gt_rim_to_pred_p95_mm`；CSV 字段为 `rim_gt_rim_to_pred_p95_mm`。RimCover-P95 只是展示名称，不建第二套定义。锁定 NumPy 版本与 quantile 的 `linear` 约定，并做历史字段一致性测试。

这是 defective-side 采样接触带到 implant 的单向距离，不是解剖轮廓 HD95。即使 P=G 也不必等于零；应报告该指标的 GT-self reference，以判断 sampling/band 下界。

### 4.2 汇总单位

先算每个 case 的 RimCover-P95，再对同一 skull 的五种缺损取等权平均，再对 skull 取等权平均。不能把所有 rim 点合并后取一次 P95。主效应定义为候选减对照，负值更好。

同时报告病例中位数、病例值的 P90/P95、五种缺损类型分层和每 skull 差值分布。注意“每例 rim 点距离 P95”和“病例主指标的跨病例 P95”是两个不同统计量。

### 4.3 风险与整体质量终点

固定报告：

- `ZeroContact2mm = 1[|R_P|=0]`，病例数及至少一例事件的 skull 数。
- 历史 disaster：核心几何指标非有限或 contact HD95 >50 mm；另分列几何零接触与数值失败来源。
- Implant CD-L1、两个方向的平均最近距离、HD95、NSD@1 mm。
- Final CD-L1、HD95、NSD@1 mm；Final 合成与点数沿用统一 evaluator。
- contact footprint precision=`|R_P∩R_G|/|R_P|`，recall=`|R_P∩R_G|/|R_G|`；R_P 为空时 precision 记 0，recall 为 0，事件另列。
- predicted contact 点数、GT contact 点数、implanted points 的离群与分布诊断。

几何 contact HD95 在 R_P 为空时可为 NA，但不能从 disaster/零接触计数中消失。非有限预测或空 P 是运行失败；无 R_G 是数据/评价不可定义，不是模型成功。P0 应先发现并解决；不允许候选运行后按模型表现选择性排除。

### 4.4 工程护栏与最小实际意义

开发阶段沿用以下观察均值护栏，相对同期 B0：Implant CD 增量 ≤0.10 mm；Final CD 增量 ≤0.10 mm；Final HD95 增量 ≤0.50 mm；Final NSD@1 下降 ≤0.01；零接触和灾难计数均不得增加。分折及合并结果都展示，不能只展示满足条件的聚合方式。

首版把 RimCover-P95 平均改善 **至少 0.10 mm** 作为值得扩大投入的工程目标。以上是事前选择的资源决策阈值，不是文献证明的临床容差。若 P0 重复采样审计显示 0.10 mm 小于测量不稳定度，必须在查看新候选效果前修订并锁定，不在结果出来后挪阈值。

最终“观察性护栏通过”和“统计非劣”分开陈述。若要正式声明工程非劣，需相应劣化量的单侧 95% 上限低于预设界值；若不能满足，仅报告点估计与区间，不宣称非劣。稀有灾难率不因观察次数相同或全零而视为总体风险已被证明。

### 4.5 表面与体积评价

首阶段只围绕固定采样的 point-surface 终点做选择。任何 voxel SurfaceDice、Dice 或 mesh 指标均为冻结后补充，并使用完全相同的重建、分辨率、后处理、输入/输出点数和总时延口径。

GT 采样重建上限、surface-splat 的密度依赖须披露。表面点云协议不能直接与实体点云或体积分割论文数字作公平排名。[^2]

## 5. 模型实现契约

### 5.1 不变的基础

| 项目 | 固定设计 |
|---|---|
| 输入/目标 | `partial -> implant`，8192 →8192 |
| grouping | `center_num=[512,256]`，最终 256 proxies |
| encoder/decoder | 当前 AdaPoinTr，dim=384，6/8 层，6 heads |
| query | 256，`learned_only` |
| dense head | 当前 fc，256×32=8192 |
| denoise | 权重 0 |
| 历史额外损失 | coarse guard、local rim、trust、dense contact、hard rim queries 均关闭 |
| Mamba / symmetry | 第一阶段全部关闭 |

基础配置参考现有 `cfgs/SkullBreak_models/AdaPoinTr_implant_full100_out8192_bncal.yaml`，但新 runtime 必须用 fold-train/dev ID allowlist 覆盖原有数据 split；禁止原配置直接加载整个官方训练池。

### 5.2 Raw-local 几何残差

设原 encoder 输出 F∈R^(B×256×384)，坐标 V∈R^(B×256×3)。对每个 proxy，在原始 8192 partial 中取一个确定的 KNN32，前 16 个用于 KNN16；同距离按输入索引稳定打破平局。

输入局部描述为归一化坐标中的 `[x−v, ||x−v||]` 四维。两尺度共享 `MLP 4→32→64`，隐藏激活 GELU；各尺度 max/mean pooling 得到 128 维，拼成 256 维，经 `MLP 256→128→384` 与 LayerNorm 输出 L。保持 `H=F+α_L·w(e)·L`，不更改 proxy 坐标或数量。

`α_L` 为可学习标量，初值 0.01，不施加 weight decay；`w(e)=min(max(e/20,0),1)`。同一约定用于 query 残差 α_Q。小初值不保证训练全过程幅值小，因此必须记录 α、残差 RMS/主干 RMS 和梯度。非有限值停止；有限但幅值变化只报告，不依据 dev 指标自动改系数。

所有新 MLP 的隐藏激活统一为 GELU，末层不加激活；新 Linear 权重采用截断正态 std=0.02、bias=0，LayerNorm eps=1e−5、初始 weight=1/bias=0。新模块不加 BatchNorm 或随机 dropout。公共主干维持原初始化与实现，不被新增模块的初始化递归重新抽样。

A1/Q0/QC 均用 H 进入原 `increase_dim`、global feature、`coarse_pred` 与 decoder memory。因而局部残差的间接 coarse 作用在这三者中是匹配的。

KNN 的邻域索引可以离散，但这里没有按预测接触分数选 top-K、替换 query 或施加 assignment。应准确称“去除 hard contact selector”，不声称网络所有操作都连续。

### 5.3 接触监督

原始 partial 标签 `y(x)=1[d(x,G)≤2 mm]`，距离在物理单位计算。proxy 标签为 `Y_i=max(y(x): x∈KNN32(v_i))`。

分数头输入 `[H_i, PE(v_i)]`，其中 PE 为当前 384 维位置编码，采用 `MLP 768→128→1` 与 sigmoid 得到 p_i。名称为邻域接触支持分数，不解释为中心点概率或校准置信度。

每例 BCE 先对存在的阳性/阴性类分别求均值，再对存在的类别平均，最后病例平均。全阴性或全阳性时只用存在的一类，不除以零、不删除病例。不新增 focal、Dice、ranking、top-K 或 rim distance 损失。

训练总损失为原始重建损失加 `λ_scf L_scf`。λ 不通过 dev 调参；按下一节的固定 train-only 零更新规则确定。A1/Q0/QC 在同一 fold 使用相同 λ。

### 5.4 辅助损失量级校准

这是后续需要单独授权的固定次数训练数据诊断，不是本次已执行事项。每 fold 从 train allowlist 按固定 salt 的 source hash 取前 4 个 skull 的全部 20 cases，以固定顺序组成 5 个 batch、batch=4。仅 seed 0 的 A1 初始副本参与；在 eval 模式下启用 autograd，临时前向使用 w=1，参数、BN buffers 均不更新。

对每个 batch，计算原重建损失与 SCF 损失相对公共 encoder 输出 F 的梯度 RMS，记 g_rec、g_scf。设 `λ=clip(0.1×median(g_rec/g_scf), 1e−6, 1)`，保存未裁剪值、最终值、5 个梯度比及输入 hash。g_scf=0、非有限或输入不合格则停止，不用反复随机初始化来得到理想 λ。

固定计算量为 5 次 forward、每次分别计算两项输出梯度，共 10 次 autograd 求导；不得追加校准训练、optimizer step 或循环搜 λ。α_L/α_Q 的校准前后值及全部 buffers 必须一致。

所有 seed 复用该 fold 的 λ。最终在 development84 上训练时，用相同规则重新得到 full84 的一个 λ，供所有候选及 seed 使用；不能复用 dev GT。校准只是初始量级控制，不是能保证整个训练梯度比恒定的机制。

### 5.5 Query feature conditioning

先由原 query generator 生成 coarse C 和 query feature Q。取单头 cross-attention，d_k=d_v=128；query 为 LN(Q) 的线性投影，key 为 LN(H+PE(V)) 的投影，value 为 LN(H) 的投影。

\[
E_{ji}=\frac{(W_q LN(Q_j))^T(W_k LN(H_i+PE(V_i)))}{\sqrt{128}},
\quad b_i=\beta\log(\max(\operatorname{sg}(p_i),10^{-4})).
\]

\[
Z=\operatorname{softmax}(E+b)V_{attn},\qquad
Q'=Q+\alpha_Qw(e)\,LN(MLP_{512\to384\to384}([Q,Z])).
\]

QC β=1，Q0 β=0；sg 表示仅在 bias 路径停止梯度。bias、softmax 使用 FP32，attention dropout=0。第一版不增加 query-specific distance gate、温度搜索或 learnable β。

插入点是原 `mlp_query` 后、原 decoder 前，保留 decoder 的全局 memory 访问。C 不在此处移动。固定上游状态时 Q0/QC 的 coarse 必须相同；端到端训练后的 coarse 可以因共享梯度间接变化，应单独分析。

AdaPoinTr、TAPCNet 与 ProxyFormer 均使 query/proxy 成为合理干预位置，但本公式仍是待验证设计，不因位置类似就已有效。[^3][^4][^5]

## 6. P0：锁定与表示审计

### 6.1 无 payload 的锁定事项

先核对代码版本、上传文档、操作规范、元数据访问范围、split 文件位置和来源。锁定文件包含：protocol、candidate matrix、metric contract、statistical plan、source ledger、run matrix、环境与代码哈希、资源上限、数据访问与排除清单。

没有 `.git` 时使用内容 manifest；不得在服务器自动 `git init`。本机规范仓库的 commit/tag 由本机流程处理，不能把历史 commit 当当前服务器已核验的代码身份。

### 6.2 需要单独数据访问授权的审计

仅对 development84，核对固定点数、有限值、归一化来源、物理 scale、GT rim 非空、样本和来源去重。确定真实 grouper 输出为 256 proxies，再审计原始 rim 被 KNN32 联合覆盖的情况。

每例至少记录：原始 positive 数、positive proxy 数及比例、原始 positive 被所有邻域联合覆盖的比例、邻域物理半径分布、proxy 中心到正点的距离。按五缺损类型和 skull 汇总。

首版的保守表示 gate：所有病例 R_G 非空；所有病例至少一个 positive proxy；每例同时存在 positive 和 negative proxy。此 gate 只用于确认首版标签可学习，不声称是补全必要条件。

不通过时不扩大 K 重试。先区分 raw sampling 缺少接触、proxy 邻域未覆盖、标签饱和三类，形成一次修订建议；修改 K、半径、标签或 proxy 数均建立 v1.2，并重新获得实施/数据授权。第一版不进行自动选参。

同时将 GT implant 自身作为 P 的 reference，记录 RimCover 的非零基准；如需重复采样或密集表面审计，单列数据生成权限，不改已有 NPZ。不得读取 confirmation、official 或 MUG sealed payload 来调表示。

## 7. 验证与资源门槛

### 7.1 L1：代码与非执行验证

后续授权范围宜限于新模块、配置生成器、指标包装与测试，不改冻结旧结果。新增代码应默认关闭，B0 的无新增模块路径必须保留。

建议模块放在 `models/cranial_scqr/`，配置放在 `cfgs/SkullBreak_models/cranial_scqr_v11/`，测试与运行工具放在 `tools/` 和 `scripts/`。具体文件列表在实施授权中确定；本计划不创建这些实验文件。

### 7.2 L2：零更新 preflight

固定人工输入、次数和新输出目录后，验证：shape、finite forward/backward、空类损失行为、mm scale、参数和 buffer 不变、optimizer_steps=0、model_updates=0。不得执行 optimizer step；不能因处于 train 模式而默许 BN running statistics 被修改。

必要用例包括：β=0 与普通 attention 一致；常数 p 的 bias 抵消；α_Q=0 退化到无 query coupling；同权重下 feature-only 不直接移动 coarse；GT 删除/置乱不影响推理；instrumentation 开关不改变输出；KNN 平局规则；RimCover 与旧字段逐例一致；无预测 contact 时 primary 仍可计算。

训练模式行为测试使用一次性克隆并比对所有 state，结果必须解释 buffers；正式零更新凭据不能只检查 optimizer。这里不做正式 latency 循环。真实 fold-train 梯度校准另列精确数据与次数授权。

### 7.3 L3：人工输入性能 benchmark

单卡空闲条件下，分别测 B=1 inference 与 B=8 forward+backward；不构造 optimizer，不调用 optimizer step。输入 8192、输出 8192、proxies/query 256、FP32，与 B0 匹配。梯度清零，eval 模式测 forward+backward 时明确它只是训练计算代理，不等于真实 train-mode step。

建议固定 20 次 warmup、每 block 50 次计时、4 个交替次序 block；输入由固定 synthetic seed 生成。明确 CUDA 同步，记录 median/P95、allocated/reserved peak memory、完整前向和训练损失计算、KNN 和所有新模块。不得只测新增 head 或排除其在线预处理。

首版资源 gate：QC/B0 的推理与 fwd+bwd 中位时延均 ≤1.50；peak allocated memory ≤1.30；绝对峰值 ≤20 GiB。所有 block 报告，不能挑最快。此为单卡预算，不是跨硬件效率证明。

如 kernel 不支持确定性，记录具体算子与容差；不能谎称 bitwise determinism。若优化了 KNN 或主干，B0/Q0/QC 同步使用该优化并重做性能契约，不能把公共优化只给候选。

### 7.4 L4：真实训练预算

| 设置 | 固定值 |
|---|---|
| optimizer | AdamW，lr=1e−4，weight_decay=5e−4 |
| LR/BN 调度 | 沿用基线并以 resolved config 锁定；不按 dev 调度 |
| gradient clipping | norm=10，沿用当前 runner |
| precision | FP32，不默认启用 AMP/TF32 或更换 CUDA 扩展 |
| batch | 8，step_per_update=1，train drop_last=true |
| epoch | max_epoch=100，标签 0–100，共 101 次遍历 |
| checkpoint | 最后 epoch；不选 best，不按 dev 早停挑权重 |
| BNCal | 仅对应 train allowlist，全量单独记录；属于模型 buffer 更新 |
| 数据增强 | 沿用实际基线输入路径；P0 锁定，不为候选单独新增 |
| seed | 开发 0；稳定性/最终 0、1、2 |

315 train cases 每轮 floor(315/8)=39 steps，总 **3939 steps/run**。full84 的 420 cases 每轮 52 steps，总 **5252 steps/run**。这些是基于无 repeat、无 resume、单卡和上述 drop_last 的预期；实现锁必须验证 loader 长度，不能仅相信配置中的 100。

真实 train-mode 吞吐与显存在获准训练的正常步骤中记录；不为测速追加 optimizer steps。BNCal 必须纳入 L4 授权，不能被视作零更新 preflight。若异常、NaN、OOM、更新计数不符或运行退出，冻结失败凭据后停止，不自动减 batch、更换精度、加载旧权重或重跑。

## 8. 分阶段执行与停止规则

### 8.1 Round A：低成本筛选

运行 B0/A1/Q0/QC × folds A/B × seed 0，共 8 个 run。只有两折全部完成并具有合法 last+BNCal 凭据后才解锁联合决策；不因单折结果中途增加候选。

进入 C/D 的必要条件：

1. 全部数值、运行和资源 gate 通过。
2. QC 相对 B0 在 A、B 两折的 mean ΔRimCover 均 ≤0，合并改善 ≥0.10 mm。
3. QC 相对 Q0 的 A/B 合并 mean ΔRimCover <0。
4. QC 相对 B0 的开发护栏在每折及合并统计均通过；零接触和灾难计数每折均不增加。

任一不满足，Round A 不晋级。混合正负折、接触增量不明确分别记 `INCONCLUSIVE`，明确恶化记 `NEGATIVE`；都不自动跑 C/D 或调 β。保守停止可能漏掉小收益，这是预算选择而非“证明方法不可能有效”。

如果 QC 不胜 Q0 而 Q0 胜 B0，记录普通 attention 路径的线索。若要转向该方向，另立协议，不把同一结果包装成 contact 成功。

### 8.2 Round B：完成四折

只有 Round A 晋级且获得新授权后，四模型补 C/D，共增加 8 run，累计 16。不要仅补 B0/QC，让完整机制表依赖选择性补跑。

四折 OOF 完成后的分级：

- `GREEN`：QC−B0 和 QC−Q0 的主指标双侧 95% 探索性 CI 上限均 <0；QC−B0 点估计改善 ≥0.10 mm；所有护栏通过。
- `YELLOW`：QC−B0 CI 上限 <0、改善达标且护栏通过；QC−Q0 点估计 <0 但 CI 跨零。可申请预设稳定性 run，不进入 Mamba/对称堆叠，不声称接触机制确认。
- `RED/NO-GO`：QC 不胜 Q0、QC−B0 无明确改善，或护栏失败。停止 SCQR-v1.1 扩展并完整报告。

以上是事前工程决策，不把开发 CI 当最终独立确认。不能因结果为 YELLOW 改 primary 或删掉坏病例。

### 8.3 Seed 稳定性

GREEN/YELLOW 且有授权时，B0/QC × folds A/B × seeds 1/2，共增加 8 run。对每 seed 合并 A/B，QC−B0 点估计应为负，观察性护栏均通过；seed 0 的同口径结果也并列，不只报三 seed 平均。

这只检查方法相对 B0 的 seed 敏感性，不伪装成 Q0 对照已经完成全四折三 seed。接触机制的多 seed 对照将在最终冻结的 B0/Q0/QC full84 训练中保留。若 seed 方向反转或风险恶化，不继续加入 Mamba，以不稳定结果结束或另立修订协议。

## 9. 统计分析契约

### 9.1 Paired skull-cluster bootstrap

开发比较从同一 split、同一 seed 的配对病例开始。每个 skull 先算五缺损平均差。固定 `bootstrap_seed=20260910`，10000 次有放回抽取 skull，计算平均差，报告 2.5/97.5 百分位区间。

开发 OOF bootstrap 在每个 fold 内分别抽取 21 skull 后合并，保留原四折权重。训练集重叠引起的不确定性仍未完整建模，因此明确标为固定预测的条件性探索分析，不声称“已消除所有交叉验证相关”。[^6]

最终三 seed 不扩展独立 N：先对每 skull 的三个配对 seed 差值平均，再对 skull bootstrap，报告对这三个已训练模型的条件性区间；另列每 seed 效应及 mean±SD。它不充分估计任意训练 seed 的总体分布。

### 9.2 主比较与次比较

正式冻结后的比较顺序为 QC−B0，再 QC−Q0。若具有合格未使用确认来源，先检验整方法，再检验接触增量，使用预注册固定序列；两项均以双侧 95% 区间上限 <0 判断改善。第一项不成立，第二项仅描述，避免任意挑显著结果。

development84 和历史暴露确认的局限必须保留，不能因为使用了上述顺序就称其完全确认性。A1、缺损类型、tail、coarse instrumentation 都是次要/探索性分析，完整报告，不按显著性选图。

灾难/零接触报告病例与 skull 计数、配对改善/恶化表及风险差区间；样本内全零时另给 skull-level 单组精确上界说明信息不足，不把退化的 bootstrap [0,0] 当确定性零风险。多项工程非劣结论须各自满足界值，不能用“不显著变差”代替。

## 10. 必须记录的机制诊断

| 层级 | 记录内容 | 解释边界 |
|---|---|---|
| 表示 | positive prevalence、AUPRC、AP−prevalence、物理邻域半径 | 高 AP 不等于生成改善 |
| 支持利用 | positive attention mass、entropy、query 间相似度 | 分数高不等于覆盖全部 rim |
| query | Q′−Q RMS、α、coarse/support 覆盖 | 同次 feature-only 不直接移动 C |
| coarse | rim-to-coarse P95、零接触、centroid/radius | 阶段定位不是唯一病因 |
| dense | primary、footprint precision/recall、implant 两向误差 | 排除只沿 rim 铺点 |
| 效率 | 整网时间、KNN、峰值显存、train 吞吐 | 不能只报告新增 head |

预注册低成本推理干预：在 QC checkpoint 上，把 bias 置零、将 p 替换为病例内均值、用固定 seed 在病例内打乱 p。它们保留参数但破坏条件信息，用于辅助判断依赖关系；不替代重新训练的 Q0，也不作为新候选选择或最终评分的替代。

干预仅在已授权开发集执行，固定次数和输入。不使用 GT p 进行正式预测；如另外安排 GT-oracle bias，必须标为不可部署上限，禁止与实际方法同表排名。

## 11. 有条件的后续分支

### 11.1 Mamba 净贡献

仅在 SCQR 有机制信号且 seed 稳定后提出独立 P2：M0=QC；M1=QC+当前低扰动 Mamba adapter；M2=QC+参数匹配 Transformer adapter。Mamba 初版固定历史 xyz、深度 2 等已知实现，不新增排序 sweep。

三者保持相同插入点、残差策略、输入 token、训练步数。M2 的参数数目用静态公式匹配，目标与新增 Mamba 参数相差 ≤10%；只允许在运行结果前通过宽度/FFN 静态计算决定，不凭 dev 结果选择。参数匹配不等于 FLOPs 或时延匹配，因此同时报告三者。

第一批 M1/M2 × A/B × seed 0 增加 4 run；若相对 M0 的工程门槛通过，再补 C/D 增加 4。M0 仅在实现、配置、数据、seed 和环境契约相同的条件下复用 QC；有任何公共优化则重新匹配。

M1 比 M0 有效但不胜 M2，不能宣称 Mamba 特有贡献。若主张效率路线，应预先指定相对 M2 的质量容差和至少 10% 整网时延改善目标；不能质量不胜后临时换卖点。未经该 P2 协议锁定，不执行这些 run。补全近邻必须讨论 CompletionMamba、FusionMamba、DAPointMamba；对称加 Mamba 的近邻还包括 Simba。[^7][^8][^9][^10]

### 11.2 中心修正

不作为 v1.1 自动补救。只有 feature-only 的识别/利用证据成立，而 coarse 仍有明确残余问题时，另拟一次 bounded center correction 方案。

该方案须固定 mm 最大位移、归一化换算、位置编码与 dense offset 基点一致性、粗细损失及额外参数对照；先 artificial zero-step，再申请真实开发实验。不得根据单个失败病例不断扩大位移。不得在最终确认之后开启并继续复用同一确认集。

### 11.3 对称性

默认非必做。先独立验证 defective-only 平面估计、供体可见性和映射置信度；不能沿用“镜像后越接近 observed partial 就越可用于补全”的单一权重。

未来设计至少比较无对称、无置信度对称、有置信度对称；分层报告 unilateral、bilateral、frontoorbital，并对平面扰动和缺少对侧证据进行压力测试。plane 的健康 GT 只用于 train/development 标签或离线误差评估，不能用于推理。

SymmCompletion 已有局部对应引导，Simba 已结合对称与 Mamba，颅骨 learned symmetry 也已有专门工作。必须将贡献落在经过实证的可靠性处理，而非组合命名。[^10][^11][^12]

### 11.4 MAE、密度损失、局部 implicit surface

均不属于当前 v1.1。MAE 需审计所有预训练 skull；密度损失须区分表面与实体表示；implicit surface 是更大的任务变化。最多选择一个有明确残余误差依据的分支，先单独协议和预算，不按固定流水线全部加上。

## 12. 最终冻结与一次确认

所有结构、损失、数据增强、后处理、checkpoint 选择规则和可选模块必须先冻结。最终候选与对照均在 development84 从头训练，train-only BNCal。最小 contact 路线保留 **B0/Q0/QC × seeds 0/1/2，共 9 个 full84 run**，全部完成、哈希冻结后才开启确认。

确认只允许对冻结 checkpoint 一次性评价；不根据结果选择 best seed、不平均点云形成事后 ensemble、不调整 β/阈值、不改后处理。重复运行仅限经核实的工具错误并有独立授权，不能因负结果重跑。

确认集资格按 §3 决定。历史暴露 confirmation20 的结果应如实标注为阶段性确认；若新来源不可获得，论文在局限中明确缺少真正新来源确认。SkullBreak official 与 SkullFix 补充实验须说明训练来源、跨域或重新训练设定、具体子集和历史暴露；不将不可比结果混入一个主排名。

最终确认之后仅做冻结、记录和报告。任何性能驱动的修改开始新研究版本，不继续称当前模型“已通过独立确认”。

## 13. 计算预算与进度

### 13.1 不含可选扩展的核心上限

| 阶段 | run 数 | 每 run 预期更新 | 累计 run |
|---|---:|---:|---:|
| Round A，四模型×A/B×seed0 | 8 | 3939 | 8 |
| Round B，四模型×C/D×seed0 | 8 | 3939 | 16 |
| 稳定性，B0/QC×A/B×seed1/2 | 8 | 3939 | 24 |
| 最终，B0/Q0/QC×full84×seed0/1/2 | 9 | 5252 | 33 |

合计最多 **141804 optimizer steps**，不含 BNCal、评估、人工 benchmark 和校准。每一阶段都可能提前在门槛处结束；这不是 33-run 批量执行许可。A0 local-only 增加 4 run；Mamba、中心修正、对称及其他论文 baseline 不包含在此上限，须重新估算总预算。

不预先承诺“一周跑完”。先由获准的人工 benchmark 和首个获准训练 run 记录的稳定 epoch 时间估计：`总训练小时≈Σ(实际 epoch 秒数×101)/3600`，再加 BNCal、评估、排队和故障余量。训练 walltime、可用磁盘和 checkpoint 保留配额均在每批启动前获准。

### 13.2 第一周以依赖关系安排

优先完成 P0 元数据与指标契约；随后在授权后实现四模型和单元测试；再分别授权零更新 preflight 与性能 benchmark。只有冻结凭据和资源 gate 全部通过才申请 Round A。该安排是工作顺序，不保证 GPU 完成日期。

开始前至少保留单 run checkpoint、恢复状态和失败日志所需空间；多个 run 的长期 checkpoint 保存范围提前列明。空间不足时停止请求清理方案，不能自动删除旧归档或训练产物。

## 14. 远程操作与产物管理

服务器项目根固定为 `/home/jovyan/adapointr_work/PoinTr`。代码和实验写入仅限该项目及另行明确授权的数据/结果目录；不进入 `/home/jovyan/aic22-4090/`，不读取凭据。

本机管理根 `E:\Codex\2026-06-06\mamba-ccf-c-1-high-resolution` 与服务器不是同一文件系统。Git commit、annotated tag、GitHub push 通常在本机规范仓库执行，服务器不自动初始化仓库或提交。任何服务器命令不得使用 E: 路径，也不得将其猜测映射到 Linux。

本机长期备份根 `E:\ResearchBackups\AdaPoinTr` 不能由远程直接验证。不得因为可能存在本机副本而删除服务器文件。只有明确确认对应四个归档文件已下载并通过哈希核验，且另外获得精确删除授权，才可删除列出的服务器归档。

长任务使用 tmux，固定唯一 run ID、新目录、stdout/stderr、开始/结束时间、PID、退出码、optimizer steps、BNCal 更新与 checkpoint SHA256。阶段门槛通过不能自动升级授权。

建议新结果目录为项目内 `logs/cranial_scqr_v11/<stage>/<run_id>/`，仅为建议；每次授权前确认不存在，禁止覆盖或复用旧输出。run record 至少包含：protocol/candidate/config/code/data/ID-list hashes、环境和 GPU、seed、起止 epoch、steps、checkpoint、BNCal receipt、primary、安全指标、性能与退出状态。

阶段冻结后经单独授权创建最小归档：协议、代码差异、配置、来源账本、指标 CSV、分析、环境、凭据和必要恢复 checkpoint；数据 payload 默认不打包。归档四件套的建议名称为 `cranial_scqr_v11_<stage>_<run_id>.tar.gz`、`.tar.gz.sha256`、`.tar.gz.bytes`、`.tar.gz.contents.txt`，实际以项目冻结归档工具输出命名为准，不混用两套格式。

交付本机文件时逐项列精确文件名、字节数、SHA256、建议目标目录，由本机完成传输和核验。本文不产生实验归档，不触发删除。

## 15. 论文证据与最终交付标准

主表至少包含 B0/A1/Q0/QC 的四折开发结果，并在最终阶段保留 B0/Q0/QC 的三 seed 匹配确认。完整给出病例与 skull 数、主指标效应、CI、风险计数、Implant/Final 指标和整网效率。

四模型矩阵解决内部归因，不足以单独支撑“优于现有方法”。论文完善阶段应另锁定至少一个近期强补全基线，优先审计 SymmCompletion 或 CompletionMamba 的官方代码、许可证、依赖及 implant-only 适配成本，运行前选定，不按本项目测试结果挑对手。若官方实现不可获得，说明限制并预先选择可复现替代，例如 ProxyFormer，不把自制模块称作原论文完整复现。按相同数据、8192 输出、训练预算和 evaluator 重新训练；原生内部结构可以不同，报告原协议与预算受限适配的差异。该项另行预算，不包含在 33-run 核心机制上限。

若宣称优于颅骨重建方法，还需加入任务专用比较并统一表面/体积评价，否则将主张收窄为 AdaPoinTr-based 表面补全改进。没有统一评估时，仅将体积方法列为相关工作，不把出版数字填入公平主表。新增比较和所有参数适配必须在最终确认前冻结。

如果后续采用 Mamba，必须有 matched Transformer 对照；采用 confidence symmetry，必须有去 confidence 对照。论文标题与摘要只包含经过实验证明的机制，不把所有计划模块写成完成工作。

图示优先展示固定规则选择的成功、失败、困难病例及 contact score、query attention 和最终误差；同时提供完整逐例表，避免用个别可视化代表整体表现。完整记录负结果、未通过 gate、预算限制、历史数据暴露和表面表示局限。

当前可申请的下一步是 **P0 的明确范围元数据/契约审计**。P0 完成后，按文件清单申请 L1 实现；依次申请 L2、L3、L4。任何阶段失败均停止并交付原因与残余权限需求。

## 16. 执行锁检查表

- [ ] 84/20 与 A–D ID 清单、source ledger 和历史暴露分级已锁定。
- [ ] 输入归一化、partial-only 推理、GT 标签边界已核验。
- [ ] 256 proxies、256 queries、8192 output 和 101 轮已通过契约测试。
- [ ] RimCover 与原字段一致，NA/空集/灾难处理已锁定。
- [ ] B0/A1/Q0/QC 的公共初始化、辅助 λ 和唯一差异已核验。
- [ ] 无偏置、常数分数、α=0、GT-free、instrumentation 测试通过。
- [ ] preflight 参数及 buffers 无更新，正式计时单独获准。
- [ ] 资源门槛、每批 walltime/磁盘配额和 run 数已确认。
- [ ] Round A/B、mixed-fold、seed 不稳定和确认失败处理已冻结。
- [ ] 本机 Git 与服务器内容 manifest 的身份对应关系已记录。
- [ ] 当前批次的独立授权、唯一输出目录和 tmux/退出凭据齐备。

未满足的项目保持未勾选，不用“方案已完成”代替实施、验证或授权完成。

## 17. 来源

[^1]: Cawley, G. C., Talbot, N. L. C. *On Over-fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation*. JMLR 11:2079–2107, 2010。[原论文](https://jmlr.org/papers/v11/cawley10a.html)。
[^2]: Wodzinski, M. et al. *High-Resolution Cranial Defect Reconstruction by Iterative, Low-Resolution, Point Cloud Completion Transformers*. MICCAI 2023。[作者全文 v2](https://arxiv.org/html/2308.03813v2)。实体点云/表面点云差异见 §2。
[^3]: Yu, X. et al. *AdaPoinTr: Diverse Point Cloud Completion With Adaptive Geometry-Aware Transformers*. IEEE TPAMI, 2023。[作者预印本](https://arxiv.org/abs/2301.04545)。
[^4]: Liu, Y. et al. *TAPCNet: Tactile-Assisted Point Cloud Completion Network via Iterative Fusion Strategy*. IET Computer Vision, 2025。[全文](https://ietresearch.onlinelibrary.wiley.com/doi/full/10.1049/cvi2.70012)。该方法有额外触觉输入，本计划没有。
[^5]: Li, S. et al. *ProxyFormer: Proxy Alignment Assisted Point Cloud Completion With Missing Part Sensitive Transformer*. CVPR 2023。[CVF 页面](https://openaccess.thecvf.com/content/CVPR2023/html/Li_ProxyFormer_Proxy_Alignment_Assisted_Point_Cloud_Completion_With_Missing_Part_CVPR_2023_paper.html)。
[^6]: Bengio, Y., Grandvalet, Y. *No Unbiased Estimator of the Variance of K-Fold Cross-Validation*. JMLR 5:1089–1105, 2004。[原论文](https://www.jmlr.org/papers/volume5/grandvalet04a/grandvalet04a.pdf)。
[^7]: Fu, Z. et al. *CompletionMamba: Taming State Space Model for Point Cloud Completion*. IEEE TIP 34:5473–5485, 2025。[机构摘要](https://research-repository.uwa.edu.au/en/publications/completionmamba-taming-state-space-model-for-point-cloud-completi/)。
[^8]: Wu, X. et al. *FusionMamba: Efficient 3D point cloud completion via spatially-aware state space models and multi-scale information fusion*. Information Fusion 134:104378，卷期 October 2026。[截至截止日可见出版商摘要](https://www.sciencedirect.com/science/article/pii/S1566253526002575)。精确 online-first 日期未核实，不声称已阅读全文。
[^9]: Li, Y. et al. *DAPointMamba: Domain Adaptive Point Mamba for Point Cloud Completion*. AAAI 2026。[官方页面](https://ojs.aaai.org/index.php/AAAI/article/view/37596)。
[^10]: Zhang, L. et al. *Simba: Towards High-Fidelity and Geometrically-Consistent Point Cloud Completion via Transformation Diffusion*. AAAI 2026。[官方页面](https://ojs.aaai.org/index.php/AAAI/article/view/38259)，[作者全文](https://arxiv.org/html/2511.16161v1)。
[^11]: Yan, H. et al. *SymmCompletion: High-Fidelity and High-Consistency Point Cloud Completion with Symmetry Guidance*. AAAI 2025。[官方页面](https://ojs.aaai.org/index.php/AAAI/article/view/32984)。
[^12]: Wodzinski, M., Daniol, M., Hemmerling, D. *Automatic Skull Reconstruction by Deep Learnable Symmetry Enforcement*. 作者预印本 2024；CMPB 2025。[作者全文](https://arxiv.org/html/2411.17342v1)。

项目操作依据为已提供的 `remote_codex_experiment_operations_guide.md` 和本机/服务器目录补充边界；历史结论与代码身份定位详见配套评审的项目证据表。本计划中的新模块宽度、β、λ 校准规则、资源门槛和停止条件是事前设计选择，不是已被论文或本项目实验验证的最优值。
