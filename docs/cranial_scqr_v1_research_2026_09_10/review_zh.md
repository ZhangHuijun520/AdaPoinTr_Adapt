# 颅骨点云补全下一阶段方案的文献评审与修订依据

## 结论

建议保留“先验证接触支持信息与补全 query 的耦合，再决定是否引入 Mamba”的主方向，但不建议按原修订稿直接启动训练。它比通用 Local–Global Mamba 堆叠更聚焦，却仍混合了尚未证实的机制解释、遗漏的关键对照、与现有代码不符的假设以及不充分的独立确认条件。

本阶段最值得验证的命题是：**在同样的额外局部特征、辅助监督和 query-attention 容量下，由 defective 输入预测的接触支持分数，是否能够改善 implant 的接触覆盖，并且不牺牲植入物整体质量。** 这与“加一个新模块是否比 AdaPoinTr 好”不是同一个问题。前者才有机会支持可信的方法贡献。

建议形成 SCQR-v1.1 的有条件正式设计：第一阶段只比较新训练的 AdaPoinTr、局部特征与辅助监督、无接触偏置的 query attention、带接触偏置的 query attention；通过之后才考虑 Mamba。对称性、中心移动、MAE 和额外几何损失不列入首轮必做项。所有可选改进必须在最终确认之前完成。

公开文献时间边界为 **2026-09-10**。研究对象是固定采样的颅骨 implant 表面点云重建，不把几何指标改善解释为临床安全、力学适配或可直接制造的证据。历史数字依据项目冻结文档和所附总结；没有重新运行数据评估或训练。正式设计见同目录 `experiment_plan_zh.md`。

## 1. 证据基础

所评修订稿为《颅骨点云补全_下一阶段实验方案_文献调研修订版_2026-09-10.md》，共 2401 行。历史依据包括截至 2026-09-09 的实验总结、全实验复盘、D2 数据协议、D5 候选训练协议和冻结事后记录。源文件及代码哈希列于文末。

以下三种结论必须分开：已知事实是冻结结果、代码依赖与论文实际机制；合理推断是 soft conditioning 可能避开 hard selector 全丢弃；待验证假设是接触偏置优于同容量 attention、Mamba 有独立增益、对称置信度能减少负迁移。

新方法有合理动机，不等于已有性能证据；没有检索到完全同名方法，也不等于证明创新空白。

## 2. 文献定位

### 2.1 通用局部—全局 Mamba 不适合作为独立核心贡献

CompletionMamba 已在点云补全中结合局部 SSM 与 shape-aware Mamba；FusionMamba 的出版商摘要明确涉及局部—全局聚合以及从原始输入提供几何修正。两者均比一般点云分类或分割工作更接近本课题。[^1][^2]

PCM、Pamba、LFE-PointMamba、CloudMamba 可作为序列化、局部建模和状态空间设计的背景，但主要研究点云分析；不能把分类或分割优势当成颅骨补全有效性的证据。DAPointMamba 确实是 AAAI 2026 的补全工作，不过研究的是无监督域适应，与单域颅骨监督补全的设定不同。[^3][^4][^5][^6][^7]

保留 Mamba 的合理标准不是“研究方向已经定了”，而是相对同预算控制具有稳定质量增益或实际效率优势。当前最终 encoder token 只有 256，不能用长序列的渐近复杂度推导整网必然更快；分组、KNN、decoder 和 dense 输出都可能主导成本。这是当前结构的工程判断，不是对 Mamba 的普遍否定。

### 2.2 Query 引导已有直接先例

AdaPoinTr 本身使用自适应 query；ProxyFormer 已围绕 missing proxies 的特征和位置建模；CompleteDT 也有局部与全局信息生成 query 的设计。普通“增强 query”不是新的研究问题。[^8][^9][^10]

TAPCNet 在 encoder 与 decoder 之间利用额外触觉点云形成 query 特征及中心，但它拥有推理时可用的额外传感信息。本方案必须从同一个 defective 输入推断接触信息。它支持“几何信息可影响 query”的设计类比，**不能证明预测出来的接触分数同样有效**。[^11]

更广泛的先例是 Mask2Former 的预测区域约束 cross-attention。它不是点云补全，也不是本方案的软偏置公式，但说明“用预测语义区域调制 query 读取”本身不是全新范式。[^12]

可能成立的差异，是特定的 partial-only 接触支持定义、避免离散接触锚点替换、接触覆盖风险的可重复改善，以及排除容量和辅助监督解释的对照。

### 2.3 对称性路线的重要近邻

SymmCompletion（AAAI 2025）已经学习局部对称变换，构造 observed–missing 对应，并以对称几何信息引导补全 refinement。只把 mirror 改成 correspondence，再加入 attention，不足以自动拉开差异。[^13]

原稿遗漏的 **Simba（AAAI 2026）** 更重要：它使用对称变换的扩散建模，并结合级联 Mamba refinement。“对称先验 + Mamba + refinement”的组合已经存在。这没有证明颅骨接触条件化无价值，但明显提高了组合式创新主张的门槛。[^14]

PointSea 通过输入自身的投影与几何自相似性构造全局到局部补全，也是“利用自身结构、区别处理不同缺失区域”方向的重要近邻。后续对称或局部精修阶段应纳入差异分析。[^15]

颅骨领域的 learnable symmetry 已用于体积重建训练和重建后的配准优化，不是简单镜像拼接。原文也讨论了跨中线缺损等困难。“颅骨对称性有价值”不等于“当前 confidence 公式合理”。[^16]

**建议对称性作为有条件扩展，不作为凑齐论文模块数的必做阶段。** 若保留，必须比较无对称、无置信度对称、有置信度对称，并验证可靠供体与不可用对侧的区分。

### 2.4 任务专用工作与表示差异

MICCAI 2023 的迭代点云颅骨重建使用正体素坐标形成实体点云，并修改 folding 解码和后处理；当前项目预测表面点云。它支持点云路线的资源潜力，但其 DACD、体积指标和高分辨率结论不能直接转移到固定 8192 点表面重建。[^17]

颅骨 deformable MAE 已发表于 EMBC 2024，“健康颅骨自监督预训练”不是自然的新颖点。它可以是后续泛化手段，但应与结构改动分开，并审计预训练来源。[^18]

Hyper-PCN 可在 CVPR 2026 官方页面核实，属于高阶相关建模补全；可支持超图作为备用表示选择，但没有直接支持颅骨接触识别的证据。[^19] SCAI-Net 提示论文需要讨论任务专用体积方法，但不能将不同数据增强、采样和后处理下的出版数字作为公平排名。[^20]

### 2.5 核验边界

| 文献组 | 支持的用途 | 不能据此声称 |
|---|---|---|
| AdaPoinTr、ProxyFormer、CompleteDT、TAPCNet | query/proxy 机制近邻 | query conditioning 首创 |
| CompletionMamba、FusionMamba、DAPointMamba | Mamba 补全近邻 | 颅骨上必然更优或更快 |
| SymmCompletion、Simba、PointSea | 对称、自结构与 refinement 近邻 | 对称 + Mamba 的组合新颖性 |
| 颅骨 symmetry、MAE、迭代点云重建 | 任务先验与表示限制 | 表面点云等同体积重建或临床验证 |
| PCM、Pamba、LFE、CloudMamba | 点云表示背景 | 替代补全任务的实验对照 |

FusionMamba 卷期为 2026 年 10 月，晚于截止日；截至截止日可见的出版商摘要可以作为公开工作证据，但不能写成“10 月已经出版并完整复现”。CompletionMamba 本次依据作者机构收录的摘要与书目，未取得可逐项审查的期刊全文。3DMambaComplete 的 arXiv 工作可确认；后续 ACM 版本存在书目线索，但本次未成功取得出版商原页核验，不以精确卷期为关键依据。部分全文不可访问，不能对其细粒度实现或消融公平性作超出可见材料的判断。

## 3. 历史结果的解释边界

### 3.1 D2 不能证明 encoder 无法影响 query

当前代码是 encoder 特征经 `increase_dim` 和 max pooling 得到 global feature，再由 `coarse_pred` 生成 coarse，随后产生 query。encoder 变化能够改变 coarse 和 query。

在 coarse 阶段观察到风险，只能说明 dense 生成可能继承风险；不能单凭观察确定唯一病因是 query，也不能证明 decoder 没有修复能力。“只有直接 query 耦合才有效”应降级为待检验假设。

### 3.2 D5 的 80.5% → 92% 是整体系统结果

冻结记录 V0 为 322/400，V1 为 368/400；但同时改变了描述符、局部与全局网络、训练目标和 selector。它证明整套 V1 的 selected-set 命中率提高，不是 context 的单独因果效果，也不是完整 implant 重建改善。

应写成“更丰富表示与集合目标的组合显示了接触识别潜力”，不能写成“已经证明上下文改善 query”或“已经定位到只差 soft coupling”。

### 3.3 D6 淘汰的是具体实现

D6 约 735 倍的性能比值来自特定固定输入、人工描述符、CPU exact assignment 和传输路径。它足够否决该路径进入当前全模型训练；不应概括为所有 assignment 或 GPU-native transport 都不可行。

也没有必要因此继续 D7/D8。当前目标是验证廉价、可部署的接触信息利用机制；soft conditioning 更适合作为一个新的有界试验。

### 3.4 命中率不是补全的必要或充分条件

至少一个 positive proxy 可能只覆盖很短的 rim；宽邻域让全部 proxy 阳性又会失去判别力。没有邻域阳性的病例仍可能通过原 AdaPoinTr 完成重建。

所以全病例零遗漏可以作为保守工程条件，但不能称为数学必要条件，更不能为了达标不断增加 K。应同时看阳性比例、原始 rim 被邻域联合覆盖的比例及局部邻域的物理跨度。

## 4. 与当前代码不一致的细节

### 4.1 最终 encoder proxy 数是 256

基线为 `center_num: [512, 256]`，DGCNN 两次下采样后返回 256 个 proxy，编码维度 384。原稿的 512 proxies 会改变覆盖、成本和与历史模型的对应关系。

首版保持 **8192 输入、256 encoder proxies、256 queries、8192 implant 输出**。改为 512 最终 proxies 必须另列 token-resolution 消融。

### 4.2 RimCover-P95 已有实现

`utils/skullfix_metrics.py` 已有 `gt_rim_to_pred_p95_mm`，evaluator 输出 `rim_gt_rim_to_pred_p95_mm`。reference rim 是 **defective 表面中距离 GT implant 不超过 2 mm 的采样点**，不是 GT implant 轮廓，也不是体积边界曲线。

应复用同一字段，将 RimCover-P95 作为展示名，增加契约测试而非重复造指标。另定义 implant-side 或密集 mesh rim 时，必须另命名。

完美预测 `P=GT implant` 时该值不一定为零，因为 reference rim 在 defective 上，允许距离 implant 最多 2 mm。最低可达误差和实际意义阈值必须考虑这个事实。

### 4.3 Feature-only 的直接与间接作用

coarse 在 query feature 之前生成；decoder 使用 `q_pos=coarse`，输出 query feature，dense head 再预测相对 coarse 的 offset。

固定权重、同一上游特征的单次 forward 中，feature-only coupling 不直接移动 coarse；端到端训练会改变共享 encoder 和 query generator，后续 coarse 仍可能改变。不能写成“feature-only 保证 coarse 不变”。

若以后移动中心，需要同步处理 query 位置输入、dense offset 基点、损失和缓存，不能只改返回数组。

### 4.4 max_epoch=100 实际是 101 轮

`tools/runner.py` 从 `start_epoch=0` 执行 `range(start_epoch, config.max_epoch + 1)`。沿用 100 就是 epoch 0–100。正式计划须记录 epoch 标签、遍历次数、drop-last 和 optimizer steps。

新计划保持当前语义并显式记为 101 轮。若以后改成 100 次遍历，必须所有匹配模型共同改变，另立版本。

## 5. SCQR 机制中的隐藏风险

### 5.1 必须增加同容量无偏置对照

F2 比 F1 多了 query-attention 路径，收益可能只是容量、额外局部融合或计算深度。

应增加 Q0：与接触候选 QC 具有相同局部特征、辅助损失、attention、输出 MLP，只把接触偏置置零。QC 对 Q0 回答接触条件化的净增量；QC 对 B0 回答整套方法的价值。

第一轮可不拆局部特征与 SCF 监督，但只能称为“联合表示组件”。若论文分别声称二者有效，必须补 local-only 对照。

### 5.2 Soft score 不等于连续空间场或校准概率

对 256 个 proxy 输出 sigmoid，没有定义任意三维位置的查询函数，也没有空间连续性约束。首版宜称 soft contact-support scores，不称连续隐式场。

`knn_any_positive` 监督的是邻域存在接触，而不是中心点属于 rim。病例内类别平衡 BCE 又改变了有效先验。分类分数不自动等于真实后验；网络置信度需要另外校准验证。[^21]

首版仅将分数用于排序和 attention bias，不用作病例接受/拒绝，也不以 0.5 解释可靠接触。概率阈值应在另行冻结的 train-only 内部校准中建立。

### 5.3 软偏置仍可能塌缩

对于内容 logit `e_ji` 和支持分数 `p_i`，接触偏置等价于：

\[
a_{ji}=\frac{\exp(e_{ji})[\max(p_i,\epsilon)]^{\beta}}
{\sum_k\exp(e_{jk})[\max(p_k,\epsilon)]^{\beta}}.
\]

所有分数相同时偏置抵消，是必要单元测试。但所有 query 共享同一支持分布，可能都关注同一小段 rim；soft 不等于具有覆盖多样性。

建议保留原 decoder 的全局读取，只通过小残差增加接触路径，报告 attention entropy、query 支持分布相似度、rim 覆盖和 dense 点分布。首版 bias 使用 `stop-gradient(p)`，由辅助监督训练分数头，避免补全损失直接将它改造成语义不明的门控；放开梯度须独立消融。

### 5.4 原对称 confidence 可能抑制有用供体

健康侧点的镜像落在缺损区时，到 observed partial 的距离自然较大。原式 `exp(-d(mirror(v),partial)^2/(2σ²))` 会把潜在有用供体降权；双侧均可见区域却容易得高分。

这是公式的几何后果。它更接近“镜像位置仍被观测支持”，不是“补全供体可靠”。后续应分别建模平面可靠度、供体可见性、映射可信度，不能只把指数符号反转，因为未观测也可能来自采样、自然孔洞或错误平面。

## 6. 评价、统计与数据边界

### 6.1 主指标合理，但需要防投机

当 predicted contact footprint 为空而预测和 reference rim 非空时，单向 RimCover 仍可定义，适合主排序；但它不惩罚远处多余点，也可能偏好沿 rim 铺点而牺牲中央结构。

必须同时报告 Implant CD、双向距离分量、HD95/NSD、contact footprint precision/recall、零接触和灾难。Final 中保留的 defective 会稀释 implant 变化，不能只靠 Final 保底。

数值 NaN、空预测、无 GT rim 和合法零接触不是一类问题。数据异常应在比较前统一处理；非有限模型输出是失败，不允许 `nanmean` 隐藏。

### 6.2 Skull-cluster bootstrap 不能消除适应性开发

同一 skull 的五种缺损必须成组保留。先病例内计算，再 skull 内平均，再跨 skull 汇总；不能把 seed×病例当独立样本。

development84 已被反复用于设计；其 CI 只能描述当前候选稳定性，不能消除选择偏差。四折训练集重叠也产生相关性。模型选择过拟合和 k-fold 方差估计的困难均有原始方法学依据。[^22][^23]

建议称为“固定 OOF 预测上的条件性、探索性区间”，结合分折展示和多 seed 检查，不称最终无偏泛化证明。

### 6.3 观察计数没有恶化不等于总体风险非劣

`ZeroContact_count <= baseline` 是清晰 gate，不等于风险差上置信限低于可接受界。20 个独立 skull 对稀有灾难率的估计非常有限。

例如独立同分布假设下，20 个 skull 零事件的单组概率单侧 95% 精确二项上界是 `1−0.05^(1/20)≈13.9%`。这不是两模型风险差区间，也不能把 100 个相关缺损当 100 次独立试验；它仅说明零观察事件不证明总体风险很低。

Final CD +0.10 mm、HD95 +0.50 mm、NSD −0.01 可作为历史工程护栏，但缺少临床或重复测量依据时不能称临床非劣界。正式非劣声明必须有明确 estimand、界值来源及单侧置信限判据。

### 6.4 confirmation20 具有历史训练来源暴露

D2 将历史 strict-train 的 104 个 skull 划为 84/20；更早 O0 ordering 记录明确对这 104 个 skull 从头训练。因此不能未经审计称这 20 个来源为从未接触的独立新受试者测试。

若新模型完全从头训练，只使用 development84，且 confirmation 结果未用于当前选择，它仍可作为“历史暴露来源上的阶段性留出确认”。若加载见过这 20 个 skull 的母模型、教师或预训练权重，则形成当前评估的直接泄漏，必须禁止。

更强的确认需要从未进入训练、教师、预训练、可视化筛选或阈值选择的新 source-level 数据。新缺损但同一健康 skull 不是新受试者。新数据与密封访问须另行授权。

### 6.5 最终确认必须放在所有修改之后

原稿 Phase 4 confirmation 后还有 Phase 5 refinement、loss、MAE，与一次确认后不修改冲突。应改为：开发与可选扩展 → 方法冻结 → 多 seed 最终训练 → 一次确认 → 报告。

确认失败也是完整结果；若再修改，需新的开发版本和确认边界。

## 7. 最小路线与投入建议

| 阶段 | 目标 | 主要产物 | 不通过时 |
|---|---|---|---|
| P0 | 数据与代码契约 | lineage、真实 token/epoch、指标与预算 | 不训练 |
| P1 | 接触条件化机制 | B0 / A1 / Q0 / QC 匹配比较 | 区分失败来源，不叠加 Mamba |
| P2（条件） | Mamba 净贡献 | matched Transformer 与 Mamba | 无独立价值则移除 |
| P3（条件） | 可靠供体或中心修正 | 单独预注册的小分支 | 不全面堆叠 |
| P4 | 最终冻结和确认 | 三 seed、匹配基线、一次确认 | 报告正负结果，不返回调参 |

P1 首轮四模型 × A/B × seed 0，共 8 个完整 run；通过再补 C/D，累计 16。继续最小稳定性与确认路线时，按正式方案计为最多 33 个完整 run。它是设计预算，不是当前授权，也不是必须跑满。

不承诺 CCF C 录用，也不强制用模块数量组织论文。独立接触增量、可复核的尾部改善、同预算对照和明确适用范围，比无法归因的多模块故事更值得投入。QC 只胜 B0 而不胜 Q0 时，应解释为普通 query refinement 可能有效，不能继续以 contact 为主要贡献。

## 8. 优先修订清单

1. 最终 proxy 改为 256，锁定主干。
2. 复用已有 RimCover，写明 defective-side footprint。
3. 增加 Q0；A1 不再称“仅 SCF”。
4. 连续概率场改为未校准 soft scores。
5. 区分 feature-only 的直接和间接作用。
6. D2/D5 因果结论降为假设。
7. 明确 101 轮与真实 optimizer steps。
8. 区分工程护栏、探索性 CI 与正式非劣。
9. confirmation20 标注历史暴露，禁止污染母模型。
10. 所有方法修改放在最终确认之前。
11. 补充 SymmCompletion、Simba、PointSea、ProxyFormer。
12. 分开 preflight、计时、训练、归档与删除授权。

## 9. 来源

[^1]: Fu, Z. et al. *CompletionMamba: Taming State Space Model for Point Cloud Completion*. IEEE TIP 34:5473–5485, 2025。[作者机构收录页](https://research-repository.uwa.edu.au/en/publications/completionmamba-taming-state-space-model-for-point-cloud-completi/)，DOI 10.1109/TIP.2025.3597041。摘要与书目证据。
[^2]: Wu, X. et al. *FusionMamba: Efficient 3D point cloud completion via spatially-aware state space models and multi-scale information fusion*. Information Fusion 134:104378，卷期 October 2026。[出版商页面](https://www.sciencedirect.com/science/article/pii/S1566253526002575)。依据截止日可见摘要与片段，未核实精确 online-first 日期。
[^3]: Zhang, T. et al. *Point Cloud Mamba: Point Cloud Learning via State Space Model*. AAAI 2025, 39(10):10121–10130。[官方页面](https://ojs.aaai.org/index.php/AAAI/article/view/33098)。
[^4]: Li, Z. et al. *Pamba: Enhancing Global Interaction in Point Clouds via State Space Model*. AAAI 2025, 39(5):5092–5100。[官方页面](https://ojs.aaai.org/index.php/AAAI/article/view/32540)。
[^5]: Zhou, B., Zhan, L., Jiang, J. *LFE-PointMamba: Point cloud learning via local feature enhancement and state space model*. KBS 329:114350, 2025。[出版商摘要](https://www.sciencedirect.com/science/article/abs/pii/S0950705125013899)。
[^6]: Qu, K. et al. *CloudMamba: Grouped Selective State Spaces for Point Cloud Analysis*. AAAI 2026, 40(11):8659–8667。[官方页面](https://ojs.aaai.org/index.php/AAAI/article/view/37818)。
[^7]: Li, Y. et al. *DAPointMamba: Domain Adaptive Point Mamba for Point Cloud Completion*. AAAI 2026, 40(8):6653–6661。[官方页面](https://ojs.aaai.org/index.php/AAAI/article/view/37596)。
[^8]: Yu, X. et al. *AdaPoinTr: Diverse Point Cloud Completion With Adaptive Geometry-Aware Transformers*. IEEE TPAMI, 2023，DOI 10.1109/TPAMI.2023.3309253。[作者预印本](https://arxiv.org/abs/2301.04545)。插入位置另以当前项目代码为准。
[^9]: Li, S. et al. *ProxyFormer: Proxy Alignment Assisted Point Cloud Completion With Missing Part Sensitive Transformer*. CVPR 2023:9466–9475。[CVF 页面](https://openaccess.thecvf.com/content/CVPR2023/html/Li_ProxyFormer_Proxy_Alignment_Assisted_Point_Cloud_Completion_With_Missing_Part_CVPR_2023_paper.html)。
[^10]: Li, J. et al. *CompleteDT: Point cloud completion with information-perception transformers*. Neurocomputing 592:127790, 2024，DOI 10.1016/j.neucom.2024.127790。[作者 SSRN 版本](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4474508)。机制依据该版本摘要，未将不同标题的早期 arXiv 版本混作同一正文。
[^11]: Liu, Y. et al. *TAPCNet: Tactile-Assisted Point Cloud Completion Network via Iterative Fusion Strategy*. IET Computer Vision 19:e70012, 2025-03-07。[出版商全文 §3.2](https://ietresearch.onlinelibrary.wiley.com/doi/full/10.1049/cvi2.70012)。
[^12]: Cheng, B. et al. *Masked-attention Mask Transformer for Universal Image Segmentation*. CVPR 2022。[作者预印本](https://arxiv.org/abs/2112.01527)。仅作跨任务的 attention 引导先例。
[^13]: Yan, H. et al. *SymmCompletion: High-Fidelity and High-Consistency Point Cloud Completion with Symmetry Guidance*. AAAI 2025, 39(9):9094–9102。[正式页面](https://ojs.aaai.org/index.php/AAAI/article/view/32984)，[作者全文](https://arxiv.org/html/2503.18007v1)。
[^14]: Zhang, L. et al. *Simba: Towards High-Fidelity and Geometrically-Consistent Point Cloud Completion via Transformation Diffusion*. AAAI 2026, 40(15):12636–12644。[正式页面](https://ojs.aaai.org/index.php/AAAI/article/view/38259)，[作者全文](https://arxiv.org/html/2511.16161v1)。
[^15]: Zhu, Z. et al. *PointSea: Point Cloud Completion via Self-structure Augmentation*. 2025。[作者全文](https://arxiv.org/html/2502.17053v1)。按可访问作者版本引用。
[^16]: Wodzinski, M., Daniol, M., Hemmerling, D. *Automatic Skull Reconstruction by Deep Learnable Symmetry Enforcement*. 预印本 2024-11-26；CMPB 263:108670, 2025。[作者全文](https://arxiv.org/html/2411.17342v1)，DOI 10.1016/j.cmpb.2025.108670。机制依据作者版本 §2。
[^17]: Wodzinski, M. et al. *High-Resolution Cranial Defect Reconstruction by Iterative, Low-Resolution, Point Cloud Completion Transformers*. MICCAI 2023，DOI 10.1007/978-3-031-43996-4_32。[作者全文 v2，2024-05-21](https://arxiv.org/html/2308.03813v2)，§2.2–2.6。
[^18]: Wodzinski, M., Hemmerling, D., Daniol, M. *Automatic Cranial Defect Reconstruction with Self-Supervised Deep Deformable Masked Autoencoders*. EMBC 2024。[机构会议论文](https://arodes.hes-so.ch/record/15644/files/Wodzinski_2024_Cranial_effect.pdf)，DOI 10.1109/EMBC53108.2024.10781853。
[^19]: Li, L. et al. *Hyper-PCN: Hypergraph-Based Point Cloud Completion via High-Order Correlation Modeling*. CVPR 2026:39121–39130。[CVF 页面](https://openaccess.thecvf.com/content/CVPR2026/html/Li_Hyper-PCN_Hypergraph-Based_Point_Cloud_Completion_via_High-Order_Correlation_Modeling_CVPR_2026_paper.html)。依据官方摘要，PDF 获取失败。
[^20]: *SCAI-Net: An AI-driven framework for optimized, fast, and resource-efficient skull implant generation for cranioplasty using CT images*. Computers in Biology and Medicine 194:110504, 2025。[出版商摘要](https://www.sciencedirect.com/science/article/abs/pii/S0010482525008558)。仅用于相关工作范围。
[^21]: Guo, C. et al. *On Calibration of Modern Neural Networks*. ICML 2017, PMLR 70:1321–1330。[原论文](https://proceedings.mlr.press/v70/guo17a.html)。重加权损失的具体判断来自本方案定义，不是该论文的颅骨实验。
[^22]: Cawley, G. C., Talbot, N. L. C. *On Over-fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation*. JMLR 11:2079–2107, 2010。[原论文](https://jmlr.org/papers/v11/cawley10a.html)。
[^23]: Bengio, Y., Grandvalet, Y. *No Unbiased Estimator of the Variance of K-Fold Cross-Validation*. JMLR 5:1089–1105, 2004。[原论文](https://www.jmlr.org/papers/volume5/grandvalet04a/grandvalet04a.pdf)。提示训练重叠的不确定性，不主张所有 OOF bootstrap 无效。

### 项目证据

项目根为 `/home/jovyan/adapointr_work/PoinTr`，以下均是既有记录。

| 证据 | 项目内定位 |
|---|---|
| token 数、基线 | `cfgs/SkullBreak_models/AdaPoinTr_implant_full100_out8192_bncal.yaml` |
| coarse/query 依赖 | `models/AdaPoinTr.py`，`PCTransformer.forward` 与 `AdaPoinTr.forward` |
| rim 定义和输出 | `utils/skullfix_metrics.py:184`；`tools/evaluate_skullfix_implant.py` |
| epoch 与更新 | `tools/runner.py:286`，`range(start_epoch, config.max_epoch + 1)` |
| 104 → 84/20 | `docs/mamba_o0_multiseed_posthoc_next_experiment_protocol_implementation_zh.md` |
| 历史训练池 | `docs/mamba_adapter_v11_ordering_ablation_preregistered_protocol_zh.md` |
| D5 多因素变化 | `docs/mamba_v15_d5_candidate_training_preregistered_protocol_zh.md` |
| D5 结果 | `docs/mamba_v15_d5a_seed0_csv_posthoc_protocol_v1.json` |

审核时 SHA256：

```text
2d0e8e118e7cd907d12bfa4d3e29ec525e12d00c5e77ee8b74ed8d072be46331  颅骨点云补全_下一阶段实验方案_文献调研修订版_2026-09-10.md
7a7791ffeebbed9c359c379a5b9e8b4f897493e3603681ff166bf80bc88d43ac  models/AdaPoinTr.py
0c4342cd19fb19a659302b0e350c3be34bd21447d2034bdc9d2e81a180174ee5  utils/skullfix_metrics.py
e5d381a578cb1e654d611f3e583d754ab3fdfe18f7a2314bd3f78869a45ae986  cfgs/SkullBreak_models/AdaPoinTr_implant_full100_out8192_bncal.yaml
```
