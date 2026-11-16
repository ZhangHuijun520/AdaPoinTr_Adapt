# Cranial-BCSP-FullMamba：SCQ-RIVE 正式实验计划书

> **实验名称（中文）**：SCQ-RIVE：空间重查询增益复核与反馈失效归因实验  
> **英文名称**：**SCQ-RIVE — Spatially Conditioned Query: Re-query Increment Verification and Error Attribution**  
> **文档类型**：科研实验预注册草案 / 实施计划（Markdown）  
> **编制日期**：2026-11-15  
> **证据截止**：截至 2026-11-15 已上传的 SCQ-DAC、SCQ-RF、SCQ B/S、FullMamba 与 P0–P2 报告，以及本次核验的公开论文  
> **当前状态**：**仅提出实验计划；未执行 RIVE 训练、预测、评分、bootstrap、外部验证或正式判门。**

---

## 执行摘要：为什么本轮不再研发新的门控公式

**建议的首轮工作不是继续尝试 DAC-2、第三次残差或损失调权，而是使已经具有开发性增量的 RF-Requery 经受一次真正同设备、相同数据、匹配训练合同的复核。** 这有助于将“在一个训练实例上观察到有效”提升为“该结构比较在可控复现条件下仍具有证据”，并为随后区分反馈位置错误、完整形状漏覆盖和接口失配提供稳定母版。

核心判断：

1. **SCQ-RF 的实证价值仍在**：历史 C 折同 GPU 的 `RF-Requery − RF-Static` 来源等权 E_P95 为 **−0.687 mm**，J_P95 为 **−0.633 mm**，J Cover@2mm 为 **+6.05 pp**，E 来源胜负 **17/4**；D 折描述性均值方向同向，但 **RF-Static_D 训练曾更换 GPU UUID 和驱动**。这些是已有开发性证据，不是本轮新结果。
2. **SCQ-DAC v2 当前公式已排除为优先投资候选**：固定 20 例、零新训练下，5,120 个 Query 的旧/新残差方向余弦全部为正，两折均值约 **0.9761/0.9739**，新邻域权重约 **0.9881/0.9870**；相对 RF-Requery，E_P95 仅改善 **0.102/0.021 mm**，J Cover@2mm 却下降 **0.196/0.306 pp**，严重病例 **3/2** 均未挽回。该结论**仅适用于冻结权重、固定公式与压力样本**，不能伪称“DAC 已重训失败”或“所有一致性设计无效”。
3. **最紧迫的证据短板是可复现性与归因**：RF 的单训练 seed、跨设备 D 核心比较、反复使用开发集，以及未保存全部预测的实际 Memory/N0/N1，使其不适合现在直接成为稳定论文创新的最终定论。
4. **最关键的科学问题仍在**：重查询带来的邻域改变何时对生成骨块有帮助，何时出现 `Q0→Q1→Q2` 持续远离，何时位置改善却 E/J 漏覆盖？不能把质心拉近等同于补全成功，也不能把方向余弦当概率化可靠性。
5. **本轮的总目标是验证、解释和决策**，而不是为了产生一组更好看的均值继续改结构。只有通过验证，才可单独立项研究结构化 coarse 覆盖或输入条件下的可靠反馈。

### 拟定阶段与训练预算

| 阶段 | 首要问题 | 主要内容 | 新增完整训练 |
|---|---|---|---:|
| R0 | 真实资产能否恢复？ | 六权重与实现、数据分折、评分及 CUDA 合同核验；历史问题表 | 0 |
| R1 | 是否能严格比较？ | 同设备同 Fold 的 RF-Static / RF-Requery 代码、初态、批次和监测准入 | 0 |
| **R2** | **重查询增益能否复核？** | **Static/Requery × Fold C/D × train_seed0**，完全同设备匹配 | **4** |
| R3 | 复核效应的内容及风险？ | 每臂 105例/折 Native、全 210 例配对 E/J 与风险、阶段记录和来源级统计 | 0 |
| **R4（条件式）** | **是否具有训练 seed 稳定性？** | 采用预登记额外 seed，例如 train_seed1；Static/Requery × C/D | **4** |
| R5（条件式） | 未解决问题发生在哪里？ | 限定的实际 Memory 邻域/更新轨迹诊断、分组反例、无 GT 推理依赖核验 | 0（原则上） |
| R6（另行授权） | 能否形成论文级比较？ | 额外 seed、独立来源/SkullFix、公平适配强基线和局部/整体评价 | 待定 |

**预算纪律**：初始授权上限是 R2 的 **4 次完整训练**。R4 的 4 次、任何新机制训练、F 等容量归因和确认集访问都不是自动批准项；需要依照冻结结果与单独决策启动。不得为了达成目标在同一开发集上无穷追加随机种子/搜索阈值。

---

## 1. 证据分层与科研问题边界

### 1.1 研究对象

定义完整骨实体为 \(C\)，残缺后的剩余实体为 \(D\)，被移除的实体骨块为 \(G\)。现行任务为：

\[
\boxed{\partial D \longrightarrow \partial G},\qquad C=D\cup G,\quad D\cap G=\varnothing.
\]

输入是**残余骨组织的完整暴露边界点云**，可能包括外板、内板、孔道/空腔及实体缺损切壁；输出是**完整缺失骨块的边界点云**，包含原有自由边界 \(E_G\) 与与残余骨接触的切除面 \(J_G\)。它不是单纯预测颅骨外板的一块缺失点云，不是完整头骨输出，也不是闭合、可制造的临床植入体模型。

禁止在本阶段以“修复真实临床植入体”替代已经定义的合成实体骨块补全任务。对内外板与切壁的引用，是对数据表面语义的解释，不意味着 8192 点能够完整解析所有薄壁特征。

### 1.2 本阶段所根据的原始报告

- **主要证据 A**：《Cranial-BCSP-FullMamba：SCQ-DAC完整实验报告》（2026-11-15，v1），尤其第 8.2–8.5、9.1–9.5、11、12 章：固定 20 例反事实 DAC 不晋级；六run DAC **没有**执行。
- **主要证据 B**：《Cranial-BCSP-FullMamba：SCQ-RF完整实验报告》（2026-11-15，v1），尤其第 4、6、8、9、11、12 章：三臂两折六次 scratch 训练；C 同设备；D 的 Static 设备混杂；新邻域确有信息差异且存在多样失败。
- **历史证据 C**：《SCQ B/S 阶段正式实验报告》（2026-11-14）：SCQ 大幅补偿常有效，`Qraw` 偏位不是失败专属；显式相对几何的独立作用 **尚缺 F 对照**。
- **历史证据 D**：FullMamba、P2、P1、P0：全 Mamba 架构已实现；仅修正质心与半径不保证完整边界及接触面改进；过往 SCQR/Rim 研究跨任务与协议，不与当前 E/J 数值相加比较。

**证据等级**：A/B/C 是用户提供实验报告中的冻结摘要；公开论文用于设计动机和竞品定位；本计划中的 RIVE 结论、门槛和方向只是**拟执行/拟验证**。未读取原始 checkpoint、全量 NPZ 或服务器现场之前，不能声称已独立核验所有 SHA 或重算 E/J。

### 1.3 已经可以说与不能说的话

| 命题 | 当前许可的表述 | 不允许的外推 |
|---|---|---|
| FullMamba | 当前实现没有保留 Transformer Self/Cross Attention，且 F0/LQI/SCQ/RF 已经训练运行 | “整个网络任何算子都是 Mamba”、“已证明全模型严格线性复杂度” |
| RF | 历史 C 同设备 Requery 相对 Static 有开发性增量 | “两折都已严格同设备复现”、“临床可靠” |
| DAC | 固定权重反事实方案无足够继续训练动机 | “六次 DAC 训练已证明失败”、“所有方向一致性不可行” |
| Qraw | 可与大幅残差形成有效联合生成；大 Qraw 位置偏移常见 | “Qraw 是所有灾难的唯一根因” |
| 接口 | E/J 距离和 2mm 覆盖是合成实体边界研究指标 | “对应临床切口间隙、厚度、制造合格率” |
| 数据 | C/D 42 个开发来源、同折来源分组无泄漏 | “42 次独立训练复现”、“此前未暴露的盲测” |

---

## 2. 文献核验与本阶段创新边界

### 2.1 已核验、直接影响当前路线的文献

| 文献 | 可核验的研究侧重点 | 对本阶段的作用 | 不能直接声称的内容 |
|---|---|---|---|
| Fu 等，**CompletionMamba**, *IEEE TIP*, 2025, DOI `10.1109/TIP.2025.3597041` | 局部 SSM、点云短/长程依赖、shape-aware Mamba | 提醒“邻域编码 + 全局形状”已被研究；必须展示与自建 FullMamba 的具体区别 | 首次用邻域或形状信息条件化 Mamba |
| Li 等，**DAPointMamba**, *AAAI 2026*, DOI `10.1609/aaai.v40i8.37596` | 点云序列化损伤空间拓扑，跨域 patch 扫描与空间/通道对齐 | 强调对应关系的实际作用，避免把 xyz 排序当稳定空间拓扑 | 该跨域方法已在 BCSP 颅骨上验证 |
| Wu 等，**FusionMamba**, *Information Fusion*, 2026, DOI `10.1016/j.inffus.2026.104378` | 局部–全局空间 SSM、残差几何对齐 | **最邻近创新性风险**：残差几何校正已被提出，论文创新须落在可重复的重查询/条件路径及颅骨实体界面场景，不能只叫“几何校正” | 现有 RF 在论文 SOTA 上已超越 FusionMamba |
| Li 等，**3DMambaComplete**, arXiv 2024 `2404.07106` | HyperPoint 生成、展开和重建 | 说明完整结构展开需要独立验证，不能把 coarse 质心对齐当全形状完成 | 其训练协议或 implant 目标与本项目相同 |
| Kwarciak 与 Wodzinski，**MedPCFM**, arXiv 2026 `2606.24433` | SkullFix/SkullBreak 医学点云、PTv3 确定性和 flow matching / diffusion 比较 | 强化以后必须包含**任务适配的 PTv3 强基线**；先确认其输出定义、划分和训练协议是否相容 | 将论文跨协议 CD 直接与本项目 world-mm E/J 排名 |
| Wodzinski 等，MICCAI 2023 `10.1007/978-3-031-43996-4_32` | 低分辨率迭代点云补全用于颅骨重建 | 说明多阶段 coarse 修复已有研究基础；RF 的创新不能只是“迭代” | RF 是首次使用迭代的颅骨点云补全 |
| Wodzinski 等，*CMPB* 2025 `10.1016/j.cmpb.2025.108670` | 可学习的颅骨对称性 | 对称性是后续独立备选条件，不应未经诊断加入 RIVE | 对称性对所有 bilateral 和 frontoorbital 缺损都有效 |
| Pathak 等，*ICCV* 2025 `10.1109/ICCV51701.2025.02355` | 真实点云拓扑与合成 benchmark 差异 | 提醒 BCSP 的输入是特定采样协议，不应将内部开发提升直接当真实世界泛化 | 工业 RealPC 与颅骨数据可直接混合评分 |
| Kodym 等，*Data in Brief* 2021 `10.1016/j.dib.2021.106902` | SkullFix/SkullBreak 数据来源与缺损构造 | 约束来源级划分、合成与临床区别 | 开放84来源等于论文官方全数据、官方私有测试集可随意使用 |
| Fishman 等，*IJCARS* 2024 `10.1007/s11548-024-03068-4` | 临床植入体厚度与 Rim 设计 | 确认临床植入体目标不等于合成缺失骨块 \(\partial G\) | J Cover@2mm 就是临床接触/厚度合格 |

### 2.2 与用户文献库的衔接

用户已整理的方向包括**颅骨缺损直接预测、对称性、点云扩散、迭代补全、CompletionMamba、3DMambaComplete、PPC-MT、DAPointMamba、FusionMamba、PPC-MT、SymmCompletion、StruMamba3D、Hyper-PCN、GenPC、RDS-Net 等**。本轮优先使用与具体 RF 归因问题相关、能找到可信公开出处的工作；其他题目继续保留在待阅读全文的创新性检查清单，**仅从用户提供标题不能声称逐篇全文核验或其精确方法细节**。

特别关注与当前 RF 最可能重合的四个要素：**(a)** 位置条件 Query、**(b)** KNN/patch 重新匹配、**(c)** 几何残差 refinement、**(d)** 方向/可靠性组合。对这些要素应在论文阅读矩阵中逐条标注“已有机制、当前实现、功能差异、是否需要额外消融”，不能凭模块更名制造创新。

### 2.3 明确区分文献证据与研究假说

- **文献支持的事实**：局部/全局联合建模、空间序列化和分层重建是点云补全重要技术方向；医学颅骨补全已有更强的 PTv3 和生成模型基线。
- **本项目的事实**：RF-Requery 的某个已冻结模型在开发 C 折改善，D 折存在匹配缺口；DAC 旧新建议余弦高度同向，但未改善压力病例的完整几何。
- **尚待验证的解释**：重查询是否普遍提升空间条件利用；不利的第二步位移是否可由推理可得的 Memory 特征辨别；新的结构化 Query 或覆盖机制是否能解决剩余误差。

### 2.4 参考文献（可定位的原始入口）

1. CompletionMamba — <https://doi.org/10.1109/TIP.2025.3597041>；摘要与方法见 <https://research-repository.uwa.edu.au/en/publications/completionmamba-taming-state-space-model-for-point-cloud-completi/>。
2. DAPointMamba — <https://doi.org/10.1609/aaai.v40i8.37596>；AAAI 正文入口 <https://ojs.aaai.org/index.php/AAAI/article/view/37596>。
3. FusionMamba — <https://doi.org/10.1016/j.inffus.2026.104378>。
4. 3DMambaComplete — <https://arxiv.org/abs/2404.07106>。
5. MedPCFM — <https://arxiv.org/abs/2606.24433>。
6. High-resolution Cranial Defect Reconstruction… — <https://doi.org/10.1007/978-3-031-43996-4_32>。
7. Automatic Skull Reconstruction by Deep Learnable Symmetry Enforcement — <https://doi.org/10.1016/j.cmpb.2025.108670>。
8. Revisiting Point Cloud Completion… — <https://openaccess.thecvf.com/content/ICCV2025/html/Pathak_Revisiting_Point_Cloud_Completion_Are_We_Ready_For_The_Real-World_ICCV_2025_paper.html>。
9. SkullBreak/SkullFix — <https://doi.org/10.1016/j.dib.2021.106902>。
10. Thickness and Design Features of Clinical Cranial Implants — <https://doi.org/10.1007/s11548-024-03068-4>。
11. CDRMamba — <https://doi.org/10.1016/j.bspc.2024.107376>；**其主体是 3D U-Net 与 Mamba 的体数据 CMF 重建，不能与本项目点云 E/J 任务直接数值比较**。

---

## 3. 正式科研问题、可证伪假设与终点

### 3.1 唯一主要问题 RQ1

> 在冻结 BCSP V1 数据、完整形状损失和 Attention-free FullMamba 主体下，`RF-Requery` 相对**同容量** `RF-Static` 的 Native E/J 以及严重风险改善，能否在 **C/D 两折均同设备匹配训练**时保持方向一致，并在额外训练种子下具有合理稳定性？

此问题研究**重查询策略的训练配置总体效果**，不是“在同一组权重下瞬间交换邻居”的局部因果效果。两模型虽然在源码中仅有邻居索引选择的结构差异，但端到端训练后 encoder、Q0、Q1、residual head 和解码器全部可能改变。

### 3.2 次要研究问题 RQ2

> 若性能发生改善或退化，这种变化能否被分解为 `Q0/Q1/Q2` 的空间放置、coarse 形状/范围、最终 dense 完整表面与 J 接触面覆盖，以及预测→GT 远端尾部等不同失败模式？

### 3.3 分支性研究问题 RQ3

> 现有推理可得 `D` 与实际 Memory Token 的空间距离、局部散度及邻域改变量，能否提供关于反馈结果的描述性信息？这种关联是否比“方向余弦高度同向”更具有区分力？

**当前不对 RQ3 注册新网络公式**，避免把未确认的关联直接制作成门控模块。不能只因为观察到相关性就宣布具有预测质量的 D-only 置信度。

### 3.4 预设假设

- **H-R1（主假设）**：在两折同设备、同训练顺序合同下，Requery 相对 Static 的来源等权 E_P95 均值在两折均不劣于 0，并至少有一折出现实际负差值和来源分布支持；并报告对应 J_P95、J Cover、CD 与逆向尾部。预设更严格、用于下一阶段晋级的研究目标为：**两折 E_P95 方向均改善，且没有新增 severe**。
- **H-R2（稳定性假设）**：若复核 seed0 支持 R1，另一个独立训练 seed 的同设备配对比较不出现明显的系统方向反转；**两粒 seed 仍不足以估计全面稳定性**。
- **H-R3（分解假设）**：某些失败以放置偏差为主，另一些以面积覆盖或接口长尾为主；单一质心/回转半径不能充分预测 E/J 成功。后续必须针对观测到的错误类型选择机制。
- **零假设/反例**：重查询没有稳定增益；仅某个训练种子有效；CD 好但 E/J 退化；平均改进同时产生新的严重失败；同设备 D 折失去历史正向结果；严重病例既有大步有效纠偏也有连续放大，无法用单一 D-only 统计量区分。

### 3.5 主要终点与风险终点

**主要效能终点**：\(\Delta E_{\mathrm{P95}}=E_{\mathrm{Requery}}-E_{\mathrm{Static}}\)，单位 world-mm，按 5 病例→来源→21 来源的原合同等权。负差值较好。

**共同报告的可靠性终点**：两折逐例 severe 的 baseline/candidate 数量、**新增/恢复/共同严重**，并按来源汇总受影响来源；severe 定义保持：

\[
\mathrm{severe}= [E_{\mathrm{P95}}>20\,\mathrm{mm}]\;\lor\;[J_{\mathrm{Cover@2mm}}=0].
\]

**解释性二级终点**：J_P95、E/J Cover@0.5/1/2mm、CD-L1、Pred→A2 逆向 P95 与 >20mm 点比例、coarse/dense 质心距离、回转半径比、`placement_tail` (dense centroid >20mm)、`compact_distribution` (radius ratio <0.9)、类型分层和预测耗时。风险阈值是历史研究标记，**不是临床容差**。

---

## 4. 固定数据、训练、评分与安全边界

| 项目 | RIVE 固定合同 |
|---|---|
| 数据 | SkullBreak 已开放 84 个来源、每来源五缺损、420 病例；不扩大为官方完整数据集 |
| Fold | C/D 每折 63 train 来源/315 病例、21 dev 来源/105 病例；C/D dev 来源不同但 train 来源重叠 |
| 任务 | 以 D-only 8192 点完整残余边界预测 G 的 8192 点完整骨块边界 |
| Coarse/Decoder | 256 coarse/query，每个 coarse 生成 32 个相对点；原 Attention-free Mamba Encoder / LQI Decoder |
| 表示、采样 | 冻结 BCSP Geo-V1 面积感知采样和点集资产；**不调 16k、输出点数、排序和 patch 采样** |
| 坐标 | D-only 归一化；Native 世界坐标 mm；禁止 GT 影响输入、排序、推理后处理 |
| 损失 | 原 coarse CD + dense CD，denoise、H1/H2、额外 J/Rim/位置监督均关闭 |
| 训练 | batch8、100 traversals、39 完整 batch/traversal、3900 steps、31200 exposures/run、300 dropped exposures/run |
| 优化器 | AdamW、lr1e-4、betas(0.9,0.999)、eps1e-8、grad clip10；实际 decay 组 5e-4/0 |
| 学习率/BN | `lr=1e-4*max(0.9^(epoch/21),0.02)`；`BN momentum=max(0.9*0.5^(epoch/21),0.01)` |
| 数值 | FP32；TF32=false；接受但披露 native Mamba 有限非位级梯度差异 |
| checkpoint | 固定 epoch99/update3900；不得开发集择优、断点续训、BNCal、TTA、后验删点 |
| 预测 | 每臂每折105个完整 batch1 Native forward；保持所有 E/J 及异常病例 |
| 外部集 | confirmation20 封存；MUG500+ 不声明高精度解剖 GT；SkullFix 另行预注册 |

**不能按文件夹名字臆断 Fold。** 历史目录存在 C/D 视觉命名与开发资产路径相反的情况；必须依据 manifest 的 source_id、fold、输入哈希与规范化元数据核查。跨来源分组在同 Fold 中不能泄漏，但由于 C/D 训练重叠和此前多轮开发曝光，两个折不等于独立训练复制或新盲测。

### 4.1 训练随机种子与数据采样种子明确分离

- `input_asset_sampling_seed = 0`：继续使用已冻结 V1 点集资产；RIVE 不重采样 8192 点。
- `training_seed = 0`：R2 的预注册同设备比较；此编号不意味着不同历史 GPU/driver 下权重位级等同。
- `training_seed = 1`：若启用 R4 的下一组训练，调整**模型初始化与训练随机流**，但 **Static/Requery 之间共享同一训练 seed、数据与实际 batch 顺序**，不得连带改输入采样资产。
- 若选择其他新 seed，必须在模型训练前写入冻结 request，不得观察某个 seed 成绩再后验选最佳。

### 4.2 数据访问与确认集协议

开发过程中仅使用当前已经开放的 SkullBreak 来源以及既有冻结 A1/A2/Ref-B 几何参考。GT 可以用于训练损失、离线评分与错误归因，**不能用于 Native 推理时的 KNN 选择、门控、坐标校正、排序、ROI、模型选择或后处理**。

confirmation20 继续封存；是否可用于最终确认，需要先核验以前的 test 曝光记录和来源独立性，预先冻结候选与全部指标，且不得在结果出来后修改模型。不能借“独立确认”名义重复使用已经调参过的开发来源。

---

## 5. R0：资产、身份和代码合同恢复（0 次训练）

### 5.1 需要读取而不是假定已存在的资产

1. 历史 RF 六个 checkpoint（每折 `S-ref/Static/Requery`），包括各自训练配置、模型 factory、权重、optimizer 组合同、batch 日志、GPU UUID、driver、完整 completion 和训练后 SHA256。
2. RF-Requery/Static 的**实际 PyTorch 计算图**及残差头实现：`Q0→Q1→Q2`、`N0/N1` 定义、`KNN(M,Q)` 方向、Local MLP、LayerNorm 的前后顺序、相对几何从当前 Query 计算的合同。
3. 在该模型中用作输入的 `M` 必须是实际 256 个 Encoder Memory Token，**不是**未经下采样的 8192 输入点，也不是 GT 的 E/J 点。
4. SkullBreak C/D manifest（train/dev 来源和五缺损）、V1 input+target 哈希、D-only 坐标中心/尺度、评分所需 A1/A2/Ref-B、固定 GT8192。
5. 评分源码/版本、历史 T0/M0/F0/LQI/SCQ/RF 分数、原 RF 全 210 开发病例风险列表，以及 DAC 固定20例诊断列表与结果。
6. 若服务器历史权重已清理，须先从**有哈希证明的本机备份**恢复到新的、隔离的只读/第三方模型目录；不能假设旧 Linux 绝对路径当前可用，不覆盖历史训练或评分日志。

历史 RF 报告曾记录六个权重的身份：

| 资产 | 历史 SHA256（仅用于恢复时比对） |
|---|---|
| S-ref C | `10502e41cd089d50b905a99bce272cee61323180c2299cc02f9f3132c012e1a5` |
| RF-Static C | `237ecd116dc8fccbfd4c0814e3ab17ff4b5fb835601de97b1e131c5c493d0a52` |
| RF-Requery C | `4816c8768da60de7c8153fcd0793524b2fb3c1dddba04de9cdf0c6eb13f2602b` |
| S-ref D | `f9c9190ea29750caf49e3d6b6c545a3e8b5912a8b6ec8fced043dafde215cc43` |
| RF-Requery D | `068288d4beb237dfe820286e22e122a5f427e4e32846c63087320aabc5b25bba` |
| RF-Static D | `c2acf8d8f8587db465e0f46dacb14cc25f10a585c3573ff7521c8eceb75bab93` |

这些值出自报告的冻结记录；**计划书编制没有现场重新算出这些哈希**。R0 必须实际逐字节验证后才可在执行报告中使用“已恢复”。预测归档、checkpoint、score CSV 和源码必须分开备份与验证，不能用“预测 tar.gz 已下载”推断六份训练权重均已备份。

### 5.2 复核模型定义（唯一结构差异）

冻结模型有 Encoder Memory \((M,F)\) 和全局特征 \(z\)，其中 \(M\in\mathbb R^{256\times3}\)、\(F\in\mathbb R^{256\times384}\)、\(z\in\mathbb R^{1024}\)，原始 learned coarse 为 \(Q^0\in\mathbb R^{256\times3}\)。

共同第一次 SCQ：

\[
N_i^0=\operatorname{KNN}_8(M,Q_i^0),\quad
\delta_i^0=h_0(\Phi(Q_i^0,N_i^0;F,z)),\quad
Q_i^1=Q_i^0+\delta_i^0.
\]

第二次校正：

\[
\begin{aligned}
N_{i,\mathrm{Static}}^1&=N_i^0,\\
N_{i,\mathrm{Requery}}^1&=\operatorname{KNN}_8(M,Q_i^1),\\
\delta_i^1&=h_1(\Phi(Q_i^1,N_i^1;F,z)),\\
Q_i^2&=Q_i^1+\delta_i^1.
\end{aligned}
\]

\(\Phi\) 保留 `z / mean LN(F_N) / max LN(F_N) / Q^1 / μ / σ / ρ` 组成的 **1802 维**描述；旧邻域只复用 **N0 的整数邻居索引**，**Static 同样基于 Q1 重新计算相对几何**。第二头均为 1802→128→3、等参数等初态。\(Q^2\) 必须进入 coarse loss、Query MLP、位置编码、排序、Decoder 邻域与 FC 中心；不得仅改返回的 diagnostics。整数 KNN 索引不求导，但由已选特征和相对坐标形成的连续路径可求导。

**关键区别**：历史 `S-ref` 已经使原 LQI Decoder 按其输入 Query 重新做局部 cross-KNN。本次 RF 研究的是 **Decoder 之前的第二个 coarse residual 的邻域选择**，而不是“原模型从未根据当前位置查询 Memory”。

### 5.3 R0 GO/NO-GO

- **GO**：四个拟训练模型均能在隔离入口实例化；source/Fold/GT 严格匹配；模型的新增参数分组正确；历史文件的期望与实测 SHA 匹配；评分器与原 RF 同源码身份；无泄漏路径。
- **STOP-IDENTITY**：权重恢复错误、实际数据清单与报告不符、Static 在代码中错误地用 Q0 几何、Requery 未真正更新 N1、评分者把病例当来源或出现无法解释的训练配置差异。
- **STOP-RESOURCE**：实际 GPU 无法运行固定 batch8 FP32 而拟采用更改 loss/点数/batch 回避。此类合同修改需**另立版本并重建两臂对照**，不能称为 RIVE 同合同复现。

交付：`r0_asset_manifest.json`、`r0_code_contract.md`、`r0_fold_leakage_check.json`、`r0_restore_verification.json`。若任何项目不满足，记录问题后暂停，不据旧 checkpoint 的目录名猜测身份。

---

## 6. R1：同设备、同初始化和数值准入（0 次完整训练）

### 6.1 设备配对原则

- **每个 Fold 内 Static 与 Requery 必须在同一张 GPU UUID、相同 driver、相同原生 Mamba/PointNet2 provider、相同 PyTorch/CUDA、相同 FP32/TF32 合同下从头训练。**
- 首选四个运行均在同一设备完成，减少折间软硬件解释复杂度。若执行过程中 GPU 必须变更，预先登记**按配对块整体迁移**：不允许只将 D 的 Static 迁移后声称 D 完全匹配。不得运行失败后自动无条件重复直至分数满意。
- 不将 GPU 同型号视为 GPU 同身份；记录 UUID、driver、container、CUDA driver/runtime、Mamba 二进制签名、CPU/内存资源日志。
- 允许硬件级非位确定性存在，但须在报告中说明；显著性能差异不能在没有证据时笼统归咎于微小梯度舍入。

### 6.2 初始化与训练顺序

- 同 Fold 两臂共有模块的参数及持久状态初始化指纹一致；第一个残差头、第二头的初态字节与结构严格配对。新增头初始化不得污染 backbone RNG 随机流。
- 同 Fold 的**实际 3900 个训练 batch**身份、来源、点集、顺序、LR、BN momentum 与优化器参数组需逐项核查。
- 两 Fold 的训练顺序原本可以不同，不要求 C 与 D 拥有相同 batch 序列，只要求**折内两臂匹配**。
- 训练时没有 `validation_selection`、`BNCal`、`TTA`、自动 resume、checkpoint 挑选或 `top-k` 重试。最后 checkpoint 固定 epoch99/update3900。
- 训练顺序提前锁定；可以使用 `Static_C→Requery_C→Static_D→Requery_D`，但不能根据 C 的 dev 成绩调整 D 的公式、loss 或配置。

### 6.3 最小 CPU/CUDA 准入

**CPU（无训练）**：

1. Q0/Q1/Q2 等 shape/dtype/batch 检验，含 batch1、batch8 和 KNN 8 邻居边界。
2. Q1=Q0+δ0，Q2=Q1+δ1 算术与返回 coarse 一致。
3. 比较 `N1=KNN(M,Q1)` 与 `N0`；相同点集/相同 Q1 的索引顺序可复现；确保 `KNN(M,Q)` 的 query/reference 方向不颠倒。
4. Static 使用相同 N0，但 `μ/σ/ρ` 是相对当前 Q1 重新计算；Requery 使用新 N1。
5. 两臂参数、state_dict 键、总参数、训练分组、无 attention 执行路径审计；不能只检查模块名称是否包含 `Attention`。
6. 归一化与 world-mm 反归一化不能因 `Q2` 替换发生二次 scale/center 或 GT 信息写入。

**CUDA 零更新（最小必要范围）**：

- 对**新迁移环境**各做真实 native Mamba batch1 推理和 batch8 前向/完整 loss/反向，检查有限值、BN 可恢复、梯度、显存、训练模式和 RNG 记录。
- 如果所有关键源码和二进制完全未变，避免重做整个已经通过的母版审计；只验证变更或迁移带来的风险。
- 若自然发生资源波动，可以披露；不因抢救显存而偷偷减少点数/训练步数。

交付：`r1_model_equivalence.json`、`r1_cpu_contract.json`、`r1_cuda_preflight.json`、`r1_exact_training_contract.json`。

---

## 7. R2：四次严格匹配的正式结构复核（建议首批唯一完整训练阶段）

### 7.1 实验矩阵

| Run ID | Fold | 模型 | 训练 seed | 同折配对 GPU | 新的完整训练更新 |
|---|---|---|---:|---|---:|
| RIVE-S0-C-STATIC | C | RF-Static | 0 | 固定 UUID A | 3900 |
| RIVE-S0-C-REQUERY | C | RF-Requery | 0 | 与 Static_C 同 UUID A | 3900 |
| RIVE-S0-D-STATIC | D | RF-Static | 0 | 固定 UUID A（首选） | 3900 |
| RIVE-S0-D-REQUERY | D | RF-Requery | 0 | 与 Static_D 同 UUID A | 3900 |

共 **4 ×3900 = 15,600 更新**；每 run 曝光 31,200 次，累计 **124,800 次病例曝光**与 **1200 次 drop**。这是拟执行预算，不是已运行数量。

本阶段不重新训练 `S-ref`，因为**唯一核心机制问题是同容量 Requery/Static 邻居重选**；历史 S-ref 仍保留为描述性实用参考，但不得用历史跨设备/不配对 S-ref 参与新的严格结构因果比较。若未来论文需证明 RF 相对第一步 SCQ 的实用增量，应追加**同设备匹配 S-ref**，并单独统计 `Requery−S-ref`。

### 7.2 与历史结果的关系

- R2 四次运行的**内部新配对差值**是唯一正式主要比较。
- 历史 C 结果 `−0.687mm, 17/21` 可作为事前设定的方向参考，但**不能要求新运行复制相同小数**；Mamba 的非位级确定性和新执行环境不能保证逐位一致。
- 历史 D 结果 `−0.766mm` 因 Static_D 设备迁移，只可作为描述性趋势。R2 D 是针对该缺口的**新匹配证据**，不应把两次 D 的差异直接解释为某个具体 GPU 造成。
- 不把 R2 的同一训练 seed 看作额外的训练随机重复：**配对消除了部分混杂，却没有给出跨 seed 方差**。

### 7.3 运行时必须保存的最小训练证据

每 run 保存：

- 实际 config、源文件/权重哈希、optimizer 组与实际 wd、scheduler/BN 参数、初态 fingerprint、训练 batch/source/样本顺序哈希。
- 3900 个 update 及 loss 日志（归一化空间的 coarse/dense 原损失口径，不混入 world-mm 评分）；最末训练曲线和异常终止原因。
- update count、exposure/drop、elapsed、GPU UUID、驱动、峰值显存、最大 RSS、资源中断和 launcher 版本。
- 固定末 checkpoint、epoch、state_dict key counts、buffer/RNG 前后证据。
- 不将训练 loss 单独下降视为完整形状改善或训练完全收敛。

### 7.4 精确的停止规则

- NaN/Inf、严重代码路径错配、GT 泄漏、GPU 设备配对违反、实际源病例乱序、loss 口径变化：**立即停止并保留错误版本**。
- 若 batch8 原生 CUDA 无法在预设预算中执行，不自动改 batch2 或累积梯度顶替；需说明训练等价性差异并重新冻结两臂。
- 模型最后结果比旧报告差不能自动重训：除非存在**可证明的执行合同故障**，否则属于应如实记录的科学结果。

---

## 8. R3：统一 Native 预测和几何评价（完整开发集；0 次训练）

### 8.1 Native 与归档

R2 完成后，固定每 run 的 105 个开发病例，batch1、`eval()+inference_mode()`，总计 **420 次新的完整模型 Native forward**。每 Fold 对两臂使用完全相同的输入点集、归一化元数据、GPU 预测环境和固定程序；没有 GT 平移/ICP、TTA、Outlier 剔除、按病例挑选输出、模型后处理或 BNCal。

**至少保存** `P8192, Q0, Q1, Q2, delta0, delta1, coarse256, prediction_id, source_id, defect_type, fold, model_id, normalization_center, normalization_scale`，并清楚注明 `Q2` 与 coarse 是同次输出；不得将不同 forward 的 Q0/Q1 与最终 P 拼接。

**建议增强且仅在资源许可时启用**：在同一次完整 Native forward 中，使用无训练影响的 hook 同时导出实际 `M[256,3]`、`F[256,384]`、`N0[256,8]` 和 `N1[256,8]`，以及无需 GT 的几何摘要。以固定样本对照验证启用 hook 后 P/Q 与未启用时在约定数值容差内一致；禁止重新执行 Encoder 再伪称来自同次 forward。若模型或资源不允许完整保存，可以只保存最小邻域整数索引与统计，并明确缺失完整 Memory 的限制。

历史报告没有完整 630 预测的 N0/N1；**RIVE 新采集不是既有记录已存在的声明**。

### 8.2 冻结评分合同

使用旧任务完全相同的 A1/A2/Ref-B：

- A1：原骨体素暴露面中心、物理面积权重，按实体邻接分配 E/J；每病例单独计算面积加权 P95。
- A2：每 A1 面四个子面中心的离散参考，用于逆向点到目标表面的距离与远端离群。
- 固定 GT8192：预测↔GT 的 CD-L1 为**未平方欧氏距离双向均值半和**，不能混入传统平方 Chamfer 或别的 CD 归约。
- 额外 Ref-B marching-cubes 参考仅作敏感度，不主张它能自动提供准确 E/J 标注。
- 所有距离恢复到 D-only world-mm；覆盖阈值 0.5/1/2mm 原封不动；20mm 风险界限原封不动。

来源汇总：每病例计算指标→同一来源五个缺损等权→每折21个来源等权。不存在把所有 reference face 合并一次性求 P95 的“总体形状 P95”。

### 8.3 输出表的最小要求

1. `case_metrics.csv`：每折每病例两臂指标，**210×2=420 模型行**，关联唯一来源与缺损类别。
2. `source_metrics.csv`：每 Fold 21来源×两臂=**84 来源行**；若添加其他参照另行计数。
3. `paired_case_deltas.csv`：每 Fold105病例×两臂差值=**210 配对病例行**。
4. `paired_source_deltas.csv`：每 Fold21来源=**42 配对来源行**；主终点在来源层比较。
5. `risk_transitions.csv/json`：Static severe/Requery severe、新发、恢复、共同严重；placement-tail、compact 同理，来源受影响数同时保存。
6. `defect_type_summary.csv`：五类型×两折，各类型21病例的描述性均值；注意五缺损共享来源，因此不是独立受试者。
7. `runtime_profile.json`：同设备测量两臂 end-to-end 推理耗时、峰值显存、参数/FLOPs（可测则报）、必要可核验的 KNN/排序耗时；不能仅比较 encoder 的理论 O(N)。
8. `scoring_freeze_audit.json`：独立核对计数、哈希、共享控制、来源折、归约和风险代数；若没有重算完整 NN，注明这是**内部一致性审计而不是独立重评分**。

### 8.4 必须完整呈现的风险转移

令 \(s_i^B,s_i^R\in\{0,1\}\) 为同一病例的严重标签：

- `new_severe = count(sB=0, sR=1)`；
- `rescued_severe = count(sB=1, sR=0)`；
- `persistent_severe = count(sB=1, sR=1)`；
- `baseline_severe = rescued+persistent`；
- `candidate_severe = new+persistent`。

此外汇报 `source_any_severe`；不要只用 candidate-baseline 净数，也不要把一来源的五个失败算作五位独立患者。既定 severe 严格大于/等于号必须与历史评分一致；边界 `E_P95=20mm` 与 `J_Cover=0` 的逻辑不能在实现时改动。

---

## 9. R4（条件式）：训练种子稳定性实验

### 9.1 启动条件

只有在 R2/R3 全部合同核验通过并完成冻结结果复核后，才召开一次独立 GO/NO-GO 判断。启动 R4 的条件应在新 R2 结果观察前先约定：**两折 E_P95 方向均改善或者一个折有可信方向改善且另一折无实质性退化，同时完整报告新增 severe；如任一折出现灾难性系统退化，暂停扩展，先分析模型身份/数值稳定性或归因。**

“无实质性退化”的数值容差如果要使用，必须在 R2 数据产生前按既有来源级波动和测量精度确定。本计划不在没有原始波动分布的情况下任意宣称 `0.1mm` 或 `1pp` 为临床/统计等价界值。

### 9.2 第二训练种子对照

建议采用预注册 `training_seed=1`：

| 模型 | Fold C | Fold D | 预算 |
|---|---|---|---:|
| RF-Static | 1次×3900 | 1次×3900 | 2 runs |
| RF-Requery | 1次×3900 | 1次×3900 | 2 runs |

总 **4 runs / 15,600 updates**。同一训练 seed 下两臂共有初始化与 actual batch 需要配对；种子变化不改变 V1 输入点集。单种子比较与下一种子比较**都应分别完整汇报，不允许只选效果好的 seed**。

### 9.3 稳定性如何报告

- 每 seed、每 Fold 的主终点变化、来源胜负/中位数、E/J、CD、风险表；不得只报告“四运行平均最小值”。
- 以 seed 为实验重复层级，报告每 seed 的四个来源级均值；只有 2 个 seed 时提供原值/极值/符号一致性，**不对 seed 总体方差下过强结论**。
- 如两 seed 方向相反，应标为**训练不稳定或研究结论不定**，不能以在同一开发集挑选另一个 seed 伪造稳定。
- 如拟继续第三个及后续 seed，单独登记上限、顺序、停止规则和成本，不在本阶段自动执行。

---

## 10. 统计分析计划：来源相关性、训练种子与多重指标

### 10.1 固定主要 estimand

对每一开发来源 \(s\)，先从五个缺损得到：

\[
\Delta_s = \frac15\sum_{k=1}^{5}\left[E_{s,k}^{\mathrm{Requery}}-E_{s,k}^{\mathrm{Static}}\right].
\]

对应每 Fold 主要报告 \(\bar\Delta_f=\frac1{21}\sum_{s\in f}\Delta_s\)（world-mm）、来源差值中位数、改善/恶化来源数。不要把 5 个缺损计作独立样本，也不要把一个 Fold 的所有体素面拼接为一个 P95。

### 10.2 探索性来源 bootstrap（R3 可实施）

建议在 R2 **训练开始前**冻结：每 Fold 从21来源中有放回采样21个来源，重复 **10,000 次**；每次带着来源内完整五缺损的差值共同重抽，取来源等权均值的经验 **2.5/97.5 百分位 95% CI**。使用记录于 config 的固定 `bootstrap_seed`，不因区间好坏切换 percentile/BCa 方案。

C/D 训练数据互相重叠，故：

- 每 Fold 单独报告 CI；
- 如展示两折42来源的 pooled 描述，可在每次 bootstrap 中**按 Fold 分层**分别采21来源并求等权平均；此区间只能作**当前固定已训练模型在当前开发来源上的描述性采样不确定性**，不能把 C/D 当独立训练试验；
- bootstrap 不能量化训练 seed 波动，也不能去除已重复使用开发集的选择偏倚，更不能赋予临床外推。

主要报告为**效应大小、区间、来源一致性与风险事件**；若需要检验 p 值，需另行预注册零假设、多重比较处理和样本量论证，不应在看到结果后为争取“显著”补做多个测试。

### 10.3 次要指标与多重检验

J_P95、J Cover@2mm、CD、Reverse P95、E Cover@2mm、Outlier>20mm、Rim/shape 分层均为辅助证据。不得把其中单个最有利指标当作新主终点；报告全部结果，优先解释**方向冲突**（例如 J Cover 增但 J P95 增）及病例级灾难。

### 10.4 效率分析

在严格同一 GPU 上固定 `warmup` 次数、同步、batch1 的 end-to-end forward、重复次数和显存记录口径；任何计时的 warmup 只用于**独立效率 benchmark**，不得加入 Native 评分或修改模型 BN 状态。输出参数量、真实推理时间、最大 allocated/reserved、KNN/排序开销、是否有 kernel fallback、理论 SSM 扫描长度。不能用 Mamba 是线性 SSM 就宣称全模型、`cdist` loss 与 KNN 也严格 O(N)。

---

## 11. R5：重查询条件与失败模式归因（诊断，不自动添加模块）

本节目标是建立**错误类型—可观察条件—可证伪解释**的连接，绝不把来源于 GT 的诊断信号直接安装进 Native 模型。

### 11.1 诊断起点：已有 SCQ-RF 的七个典型病例

优先保留以前已暴露且有完整阶段记录的固定案例：

| Fold/病例 | 历史观察 | RIVE 需要回答的具体问题 |
|---|---|---|
| C/012 parietotemporal | Q0/Q1/Q2 质心误差递增，最终极端失败 | 是一阶段共识性错误、N1 关联错误，还是第二阶段继续放大？ |
| C/025 parietotemporal | Q0→Q2 继续偏离，E/J 长尾严重 | 更新轨迹与覆盖丢失是否同向变化？ |
| C/053 frontoorbital | Static/Requery 的 Q1 就已经分化，Requery 最终失败 | 不把第二头重查询当作唯一根因；检查端到端表征变化 |
| D/069 random_2 | 质心改善，E/J 仍差，逆向>20mm可为零 | 是否以目标表面漏覆盖和收缩为主，而非远端飞点？ |
| D/087 frontoorbital | Q1→Q2 确实纠偏但未完全成功 | 第二阶段是纠偏不足还是其他曲面没有生成？ |
| C/025 random_2 | 依赖大二次更新被挽回，但 J 仍低 | 不能用固定残差小上限破坏有效纠偏；目标需兼顾接口 |
| D/008 frontoorbital | 大幅二次纠偏并形成相对良好 E/J | 用作正对照：可靠重查询在输入 Memory 上表现如何？ |

这些病例早已参与假设形成，**只能作为解释与回归测试**，不能再声称是新的独立确认样本。若新训练中其风险标签或误差走向不同，应完整保存并讨论，而非挑另一个更适合故事的个案。

### 11.2 四类失效标签：离线分类规则（研究性）

不要用一个“centroid>20mm”概括所有失败。对每个病例保存以下组合指标：

**P 类：整体放置失败**——较大 centroid offset、较多 Pred→A2 远端点、E/J 均差；在 Q0/Q1/Q2 记录中可能出现连续远离。**不只靠质心距离判断**，并指出该类标签是根据真实 GT 的离线分析，不是推理时门控。

**S 类：空间分布收缩/欠覆盖**——质心接近或正改善，但回转半径比偏小，E/J 参考→预测覆盖差，Pred→GT 的大离群未必明显。已有 D/069 属于此类解释的典型反例。

**I 类：接口专属或接口主导失配**——E 部分较好但 J_P95 或 J_Cover 仍明显差；考虑输出有限点数和 BCSP 表面 E/J 的离散参考误差，不把 J_Cover 等同真实临床接触。

**X 类：复合/不定**——位置、收缩、表面漏覆盖和 J 错误同时存在或无法可靠分解。允许同一病例具有多个标签；没有诊断必要时不要硬划为互斥四类。

以上类别仅为解释框架，**不是先验经过验证的病因模型**。如需转化为正式的类别预后预测器，须另设 D-only 信息与独立评价计划。

### 11.3 每个病例必须完成的阶段图

在相同 world-mm 坐标系，保存：

1. `D8192` + `GT G8192/高分辨率 E/J 参考` + Q0 + Q1 + Q2 + P8192 全局视图；按同案例固定坐标范围、禁止 ICP/center alignment。
2. Q0→Q1→Q2→P 的质心位置、半径比、bbox extent、到 GT8192 的有向/双向形状距离；不同点数 Q256 与 P8192 的覆盖比较必须注明点预算差异。
3. 对 E/J 高分辨率 A1 参考到 Q256/P8192 的面积加权覆盖与 P95，尤其观察极差病例是否只是整体平移或存在缺失空间范围；若 Q256 的参考覆盖远低于 P8192，不得直接解释为 Decoder 失败，因为采样点数不同。
4. 固定剖面/局部接口视图（允许使用 GT ROI **只作显示裁剪**）；完整评分不裁剪点集。
5. 阶段残差的每 Query 范数分布、分位数和空间热图，但不用 `||δ||` 大小直接等价于正确/错误。
6. 与 Static 的同病例对照：可以展示各自 Q0/Q1/Q2，但**两臂对应 query index 不保证解剖意义对齐**，不得直接以第 i 点的位置差当成同一解剖点的更新因果效果。

### 11.4 实际 Memory 邻域机制诊断

只有在 R3 的同次 Native 明确保存 `M/F/N0/N1` 之后，才可以对以下**推理可计算**的量建立病例层统计：

\[
\begin{aligned}
J_i^{\rm neigh}&=\frac{|N_i^0\cap N_i^1|}{|N_i^0\cup N_i^1|},\\
d_i^{(0)}&=\frac1k\sum_{j\in N_i^0}\|M_j-Q_i^1\|_2,\\
d_i^{(1)}&=\frac1k\sum_{j\in N_i^1}\|M_j-Q_i^1\|_2,\\
s_i^{(1)}&=\sqrt{\frac1k\sum_{j\in N_i^1}\|M_j-\bar M_{N_i^1}\|_2^2}.
\end{aligned}
\]

可选记录局部 Memory 特征的均值方差/余弦、`N0/N1` 邻域变更量与 `Q1→Q2` 残差方向范数。**这些都是由残缺 D 和网络自身特征计算的描述量，不是“地面真值可靠性”或“临床风险”**。

离线可再用 GT 计算是否几何改善，但必须严格分开两列：

| 特征性质 | 能否在 Native 推理中使用？ | 作用 |
|---|---|---|
| Memory 最近邻距离、空间离散、旧新邻居重合、网络残差 | 是，来自 D/当前网络 | 描述或未来候选 D-only 条件 |
| GT 质心误差、Q2 到真骨块方向、E/J 分区标签、离线 severe 标记 | 否，除非训练时作为监督且不输入推理 | 事后科学解释/训练损失，不用于 Native 决策 |
| 基于病例真值选择 Static 或 Requery 更优输出 | 否 | 典型 oracle leakage，禁止作为模型成绩 |

**禁止从 DAC 中继承“余弦高就可信”的假设。** SCQ-DAC 的高余弦在成功与失败压力病例都存在。若要检查新的 D-only 描述量是否与失效有关，应同时报告成功纠偏和失败纠偏的条件分布及反例，不用事后阈值人为构造 ROC/高准确率结论。

### 11.5 最小诊断样本及全量优先级

- **最优**：对 R2 四模型的 210 个配对开发病例，在同次 Native 中保存必要 N0/N1 与 Memory 数据，直接做全量离线分析，不额外 forward。
- **若资源不足**：固定 7 个旧解释病例，加按预注册字符串哈希从各折与五缺损类型抽取的病例；先定数量与规则再看新模型评分。结果限于**可行性/机制线索**，不得推广为风险发生率。
- **不满足数据合同**：在新的 R2 运行中没有保存实际 N0/N1/F，只能报告阶段 Q0/Q1/Q2/P 与输出几何，不得用原输入 8192 邻域替代实际 256 Memory 的结论。

### 11.6 有效归因与无效归因

| 允许的结论 | 不允许的结论 |
|---|---|
| 同设备 Requery 与 Static 在固定训练合同下的性能差异是结构配置的实证比较 | 训练后模型不同就表示“同权重在该病例切换 N1 必然更好” |
| 观察到了某类失败在 Q0/Q1/Q2 已存在 | 能据此唯一断言 Encoder、KNN 或 Head 是最早根因 |
| 邻域不同、条件描述量不同 | 新邻域必然解剖正确、必然更可信 |
| 质心纠正但 E/J 仍差 | 只要加强质心 loss 就能解决覆盖 |
| 反馈较大时可救回某些病例 | 所有大反馈都应被允许或所有大反馈都应缩小 |

---

## 12. 预注册 GO/NO-GO 决策树

研发门槛用于分配预算与决定可否将候选推进论文验证，**并不是临床容差**，也不能为已观察到的性能事后放宽。

### Gate 0：工程与来源合法性

**GO**：真实 checkpoint/源码/数据/划分一致，Static/Requery 同容量、同 Fold 同 GPU、各 3900 更新，训练及 Native 预定合同核验通过。  
**NO-GO**：来源泄漏、执行路径不符、不同设备混训却声称严格配对、擅改损失、P/Q 不同 forward 拼接、Native 使用 GT 配准；停止并披露。

### Gate 1：重查询增量是否可复现？

只比较 **新 R2 Static vs Requery**：

- **技术支持（继续评估）**：两折来源等权 E_P95 差值为负，来源中位数和改善数无明显逆转，J/CD/覆盖总体未出现与 E 直接冲突的系统退化，并完整展示 severe 转移。CI 作为效应精度描述，不用“p<0.05”作为唯一判据。
- **准确率正向但可靠性不合格**：E/J 指标改善，却出现一个或多个 Requery-only severe，或某类型尾部明显回退。**保留结构有效的可能性，但不晋级为可靠最终方法。** 若 R4 额外 seed 条件已被独立授权，可检验该风险是否稳定；不得后验删除病例。
- **证据不确定**：C/D 符号反转或仅一个折靠少数极端值带动平均。停止新模块训练，先检查训练轨迹/几何归因，不称“跨折稳定”。
- **结构无充分增量**：匹配 R2 两折主要 E/J 与来源分布均无一致实用收益，或严重性能明显回退。冻结负结果；不继续通过更换排序、loss、阈值制造正结果。

**严格研究晋级门槛（高标准）**：两折 \(\Delta E_{\rm P95}<0\)，J_P95 与 J_Cover 的整体方向不发生不可接受回退，**相对 Static 在 C、D 每折均 `new_severe=0`**，并保留正常/严重病例级反例说明。这是**候选晋级条件**而非确认性总体结论，不能从一个 seed 推断临床安全。

### Gate 2：是否进入额外 seed？

- 满足 Gate1 的正向/初步支持且资源可行：提交 R4 单独授权，seed1 两折两臂各一次。
- 未达 Gate1 或风险新发显著恶化：先停止扩展，完成 R5 的只读归因，不再训练“更好的 seed”来选择结果。
- 仅为了确认 D GPU 混杂，不能将同 seed 新运行误写为多 seed；R4 的训练随机流必须真正独立。

### Gate 3：是否开始新的机制创新？

| R2/R4 发现 | 科学解释的优先级 | 下一项**独立**研究（不在本轮自动实施） |
|---|---|---|
| 两折、至少两 seed 均改善但仍有新 severe | 重查询有效，残余风险不能忽略 | 用 D-only 空间支持/分布覆盖提出一个单接口、可证伪的可靠反馈机制，并设置同容量对照 |
| 位置改善但 E/J 与范围不改善 | 骨块形状分布问题优先 | 结构化 coarse 点集覆盖、内外板及 J 表面支持的独立机制，而非继续 centroid/radius 惩罚 |
| 初始 Q1 就出现大偏移，且旧新邻域几乎都很远 | 局部初始条件可能不足 | 与初始错误位置解耦的 D-only 粗区域空间提示；先做可预测性与信息支持，不直接装复杂网络 |
| 重查询跨 seed 没有增量 | RF 结构的统计基础薄弱 | 停止该方向盲目叠加，重新评价输入/损失/生成架构与强基线 |
| 显式几何独立贡献仍需区分 | 竞争解释尚未排除 | 单独规划 **SCQ 的 F 等容量几何通道控制**；不与 RIVE 四run混成同一个主试验 |

**尤其禁止**将本轮同设备复现中出现的某两个困难病例直接改成专属规则后，再在同一 C/D 上称“获得新的独立确认”。

---

## 13. 不建议立即开展的方向及原因

1. **DAC v3 的 cosine、alpha 温度、epsilon 和固定阈值扫描**：当前同一共享 h1 提案在压力样本上高度相关且共同错误，未形成可靠区别。继续扫描这些量容易迎合旧20病例。
2. **一律缩小或 clamp 所有 δ0/δ1**：C/025 random_2、D/008 frontoorbital 等历史成功案例依赖较大步校正；全局限幅无证据保证。
3. **强监督 Qraw 独立靠近 GT**：SCQ B/S 的 195/210 个 Qraw 质心>20mm 说明其可能与残差形成协同中间表示，但该偏位并非失败专属。强制改 Qraw 会改变模型分工，需另行机制论证。
4. **重做采样和 16k 输出并同时改结构**：V1 表示及采样搜索已经收束，改变点数将破坏当前 RF 归因合同；输出点数另行独立因素研究。
5. **立即叠加 GT 接口 mask、Rim loss、对称性或更多 refinement**：会把整体错误与接口提升混成多因素效果，且历史 D2/SCQR 已显示局部风险与整体形状可能冲突。
6. **把自监督一致性或点云不确定度当作天然正确性**：共享模型的两路建议可能一致地错误，需先证明可用信息和实际误差有相关性，再建立并校准置信度。
7. **用 MUG500+ STL 补成“高精度真实 implant GT”**：此前 MUG 源数据证明不足；没有新独立医学验证时不能将其作为临床高精度训练或确认参考。
8. **在 C/D 开发集上根据排名选择所谓“最优随机 seed”**：该过程直接产生选择偏倚；论文主分析必须完整纳入预设 seed。

---

## 14. 验收、风险与执行偏差记录

### 14.1 质量控制记录分层

**工程合同层**：CPU/CUDA shape、索引、loss、反向、资源和 RNG、数据路径与 manifest。  
**实验执行层**：初态/batch/更新、exit code、checkpoint、预测计数、时序与审计。  
**科研有效性层**：E/J、CD、Coverage、风险转移、来源级分布、seed 稳定性和对照归因。  
**应用外推层**：SkullFix、真实临床、闭合 mesh、厚度、接口接触、制造适用性。

前三层中的执行通过不自动升级为后一层有效；RIVE 不包含闭合实体 implant 的临床合格性评价。

### 14.2 偏差分类与必要处理

| 类型 | 记录方式 | 是否允许继续 |
|---|---|---|
| GPU UUID/driver 变化使折内两臂不匹配 | 单独标记 `DEVICE_CONFOUNDED`，保存新旧环境 | 不作为严格结构比较继续；待预授权成对重训 |
| 模型或数据输入哈希不一致 | `IDENTITY_MISMATCH` | 必须停止当前组 |
| 执行启动失败、未进入 optimizer | 保留 failed request 和详细日志；不计科学阴性 | 可提出独立修正版本，经核准再启动 |
| BNCal、loss/点数/源折变化 | `CONTRACT_BREAK` | 不允许声称与旧协议公平 |
| 正式模型几何结果不理想 | `SCIENTIFIC_NEGATIVE_OR_MIXED` | 记录完整分数，不能自动重训 |
| 汇总计算错误 | 版本化修正审计脚本，冻结原 CSV 和变更原因 | 仅核对已存在结果，不改模型/数据 |
| 20例 DAC 的已知压力样本表现与新训练不同 | `HISTORICAL_CONTEXT_DIFFERENCE` | 需区分模型/训练/样本，不以新分数篡改旧报告 |

### 14.3 资源与预算边界

历史 RTX4090D 约 3900 步运行曾出现 25–29 分钟级训练段耗时、约13GiB Torch allocated 峰值，**仅作为既有资源记录，不作为未来训练时长保证**。RIVE 必须通过现场真实 batch8 原生 CUDA 准入，并设定新设备显存、CPU RSS、磁盘剩余及总输出预算；避免无约束保留全量中间激活和多余 trace。

无论结果好坏，不自动执行服务器清理、GitHub 推送、权重下载或 confirmation 访问。任何产物移动/删除遵守单独授权；复现材料与临时 GPU 计算缓存分类存放。

---

## 15. 未来论文对比：公平任务适配与新颖性证据

### 15.1 方法应如何命名与定位

如 RIVE 复核成功且可靠性/种子证据足够，当前技术贡献可谨慎描述为：

> 在不使用 Transformer Self-/Cross-Attention 的颅骨边界点云补全网络中，提出一种**基于修正后 Query 重新查询残余颅骨 Memory 的两阶段 coarse 条件更新配置**，并使用**同容量静态邻域对照**检验其对完整骨块 E/J 重建与病例级风险的影响。

不能写成“首次提出 Mamba 点云补全”“首次利用残差校正”“全部患者可靠”“重查询具有确定的安全保证”。即便模型名称带 `RIVE`，**RIVE 目前是实验阶段名称，不是新的已训练算法名**。

### 15.2 强基线比较清单（后续独立工作）

| 参照 | 科研作用 | 必须先核验的适配条件 |
|---|---|---|
| AdaPoinTr-Implant / T0 | 初始 Transformer 合理基线 | 任务必须统一为 \(\partial D\to\partial G\)、8192/8192、相同 source/Fold/GT 参考 |
| M0（Mamba Encoder + Transformer Decoder） | 分清无 attention 迁移和 RF 后续增益 | 不混合旧 SCQR 与新 BCSP V1 口径 |
| FullMamba F0、LQI、SCQ S-ref | 自建架构逐阶段消融 | 不将跨设备历史均值称新的同设备严格对照 |
| RF-Static | **本阶段主要等参数对照** | 相同初态、设备、训练顺序与最后 checkpoint |
| CompletionMamba | Mamba 局部/shape-aware 竞争方法 | 官方输出/损失是否适配完整骨块、点数与训练预算 |
| 3DMambaComplete | HyperPoint 生成/展开竞争方向 | 是否能够生成含 J 的完整 \(\partial G\) 结构；训练/资源公平 |
| FusionMamba | 空间感知、残差对齐与多尺度竞品 | 最新 2026 方法，优先核对**源码细节和实验边界** |
| MedPCFM / deterministic PTv3 | 医学任务强基线 | SkullFix/Break 数据源可能一致但**任务表示和 E/J 终点未必相同**；需重新适配后才比较 |
| Wodzinski 2023、2025 | 颅骨迭代重建与对称性 | 比较体素/完整点云目标必须明确，必要时转换到共同评价实体 |

如没有可靠开源实现或没有授权数据，诚实标注“无法公平适配”，不要伪造复现分数或将跨论文的 CD 数字排成 SOTA 表。

### 15.3 SkullFix 与现实应用的准确定位

SkullFix V1 此前完成几何资产准备，不表示本阶段已有 SkullFix RF 训练、确认或外部跨来源验证。可在最终冻结模型后另行设计与 SkullBreak 兼容的 source-level 验证；SkullFix 有自身来源/FOV 与缺损生成差异，不能简单声称是临床真实病例。

医学临床 implant 研究还须将厚度、Rim 宽度/连续性、水密/自交、原始 CT 分割误差、实体修复与医生判断列为独立研究层级。当前任务输出点云不保证制造可用，不能从 J Cover、E P95 直接推导临床结局。

---

## 16. 数据表、代码配置和归档规范

### 16.1 建议实验目录（逻辑设计，不是当前文件系统真实存在的目录）

```text
scq_rive_20261115/
├── 00_protocol/
│   ├── SCQ_RIVE_pre_registration.md
│   ├── run_matrix.yaml
│   ├── frozen_metric_contract.json
│   ├── fold_manifest.sha256
│   ├── risks_and_decisions.md
│   └── prior_evidence_manifest.json
├── 01_r0_recovery/
│   ├── checkpoint_verification.json
│   ├── code_and_env_fingerprint.json
│   └── fold_leakage_and_path_audit.json
├── 02_r1_admission/
│   ├── cpu_contract.json
│   ├── cuda_preflight.json
│   └── initialization_pairing.json
├── 03_r2_training/
│   └── {fold}/{arm}/{seed}/
│       ├── config.json
│       ├── initialized_state.sha256
│       ├── actual_batches.sha256
│       ├── train_metrics.csv
│       ├── resources.csv
│       ├── final_checkpoint.pth
│       ├── final_checkpoint.sha256
│       └── completion.json
├── 04_r3_native/
│   ├── predictions_manifest.json
│   ├── case_npz/
│   ├── optional_memory_trace/
│   └── prediction_freeze_audit.json
├── 05_r3_score/
│   ├── case_metrics.csv
│   ├── source_metrics.csv
│   ├── paired_case_deltas.csv
│   ├── paired_source_deltas.csv
│   ├── risk_transitions.json
│   ├── source_bootstrap.json
│   └── scoring_freeze_audit.json
├── 06_r4_seed_replication/       # 仅条件式授权后创建
├── 07_r5_diagnostics/
│   ├── prespecified_cases.json
│   ├── all_case_failure_taxonomy.csv
│   └── world_mm_visualizations/
├── 08_decision/
│   ├── gate_result.json
│   ├── interpretation_boundaries.md
│   └── stage_closure.md
└── 09_literature/
    ├── source_links.md
    └── novelty_overlap_matrix.csv
```

### 16.2 核心配置模板（需根据项目源码字段逐一校验；不是可直接运行的 request）

```yaml
experiment: SCQ-RIVE
status: PLAN_ONLY
created: 2026-11-15
problem: bcsp_defective_skull_boundary_to_missing_fragment_boundary
model_family: attention_free_fullmamba
compared_models: [RF-Static, RF-Requery]
input_points: 8192
output_points: 8192
coarse_points: 256
points_per_coarse: 32
input_sampling_asset_seed: 0
training_seeds_initial: [0]
training_seeds_optional: [1]
folds: [C, D]
sources_per_fold_train: 63
sources_per_fold_dev: 21
cases_per_source: 5
batch_size: 8
traversals: 100
batches_per_traversal: 39
optimizer_steps: 3900
optimizer: AdamW
lr: 0.0001
betas: [0.9, 0.999]
eps: 1.0e-8
grad_clip: 10
weight_decay_matrix: 0.0005
weight_decay_exempt: 0.0
precision: fp32
tf32: false
checkpoint_rule: last_epoch99_update3900
forbid_gt_native_conditioning: true
forbid_tta_icp_bncal: true
forbid_dev_checkpoint_selection: true
baseline_for_primary: RF-Static
candidate_for_primary: RF-Requery
primary_endpoint: source_equal_E_area_weighted_P95_world_mm
risk_endpoint: severe_geometry_new_rescued_shared
severe_logic: 'E_P95 > 20mm OR J_Cover2 == 0'
bootstrap:
  unit: source
  draws: 10000
  level: 0.95
  method: percentile
  seed: PRE_REGISTER_BEFORE_TRAINING
additional_runs_require_new_authorization: true
```

**配置、代码和数据的可恢复性优先于过度扩张辅助审计。** 请保留足以独立复算的源代码、配置、Fold、checkpoint、预测和评分结果。若复制/备份训练权重会超出授权或空间预算，至少先确保原 checkpoint 并不因清理丢失；不要将裸哈希列表当作权重备份。

---

## 17. 实施清单与正式阶段交付物

### R0–R1（零训练）

- [ ] 真实来源级 fold 列表核对，排除同折 train/dev 重叠；记录 C/D 训练来源重叠的解释边界。
- [ ] 验证旧 RF 权重/代码/采样资产与指标源码哈希；新设备实际 CPU/CUDA batch1/batch8 检查。
- [ ] 锁定同 Fold GPU UUID、driver、native provider、初始参数与实际 3900 batch 顺序。
- [ ] 冻结模型对照、指标、风险定义、统计代码、source bootstrap seed、停止规则和输出目录。

### R2（首批4 run）

- [ ] `Static_C/Requery_C/Static_D/Requery_D` 全部 scratch、原训练合同、last checkpoint。
- [ ] 每 run 3900 条 train 更新/批次轨迹；GPU 设备合同与 checkpoint SHA。
- [ ] 禁止按 dev 表现停训、重跑或选择多个候选。

### R3（统一评分）

- [ ] 每模型105 dev 病例 Native 保存，所有严重与正常病例均保留。
- [ ] 输出 420 模型病例行、84 模型来源行、42 来源配对行（不含可选额外参照）。
- [ ] 主指标 E_P95、E/J 2mm Cover、J_P95、CD、Reverse A2、风险转移、类型差异全面报告。
- [ ] 每 Fold 来源 bootstrap 结果及其“开发来源、不含 seed 波动”限制；不得用显著性掩盖风险。
- [ ] 对 7 个已知压力/挽回病例和固定哈希对照进行同世界坐标解释。

### R4/R5（条件式）

- [ ] 是否进入 seed1 已由 R2 的冻结评价和此前预设规则裁决。
- [ ] seed1 的新增训练协议独立授权且与 R2 同一结构、输入资产、评分器。
- [ ] 若采集 N0/N1 与 M/F，确认来自同次 Native 而非新 forward 混合。
- [ ] 不将 D-only 特征关联或 GT 误差方向直接写成未经验证的可靠度模块。

### 完成时的唯一正确表述

在实际 RIVE 尚未执行时：**“已经提出 SCQ-RIVE 预注册方案，尚未得到新 RF 复现或可靠性结论。”**

若 RIVE R2 执行完成但未启动 R4：**“获得同设备的单 seed 配对开发比较；还不能声称跨 seed 稳定或独立确认。”**

若 RIVE R4 完成：**“在预注册的两个 seed、两个开放开发折上获得观察结果，仍须检查历史曝光、统计范围与独立外部确认。”**

若一部分结果为负：应报告 **“不支持稳定结构优势/可靠性目标未达”**，而不是只截取最有利的折、缺损类型或 seed。

---

## 18. 下一阶段方向的最终科研定位

本计划**不把 DAC 阶段提前定义为失败的整个研究路线**，也不把历史 SCQ-RF 的有限增量包装成已发表级结论。最应保留的逻辑链是：

1. P0–P2 表明：位置、范围和完整表面/接口质量不能被单一中心或半径指标充分代表；
2. FullMamba 已建立无 Transformer Self/Cross Attention 的实际基础架构；
3. SCQ B/S 证明逐 Query 条件残差具有开发集平均收益，但个别病例会发生严重错位；
4. RF 有证据表明重查询可能有增量，但 D 同设备复核和训练稳定性不足；
5. DAC 冻结权重诊断显示共享头两路方向相似不足以识别共同错误，**当前固定公式没有训练投资动机**；
6. **RIVE 先验证 RF 增量是否真实稳定，再通过来源与阶段归因决定究竟应改 Query 空间对应、形状展开还是接口精修。**

由此，课题应围绕的下一科研问题不是“再加入什么更复杂的 Mamba 模块”，而是：

> **在完整颅骨骨组织边界点云补全中，基于 Attention-free Mamba 的空间重查询反馈是否能稳定提升缺失骨块整体几何与切壁覆盖？哪些失败来自反馈空间条件的缺失，哪些来自 coarse 形状分布和局部界面漏覆盖？**

**正式执行建议**：先完成 R0–R1；通过后，首批只授权 **R2 四次同设备匹配训练**；评价前冻结判据与来源统计；若支持增量再实施 seed1，若不支持则收束 RF 结构结论、回到已观察失败类型来选择下一项独立机制，不继续用同一开发集调整 DAC 系数。

---

## 附录 A：避免歧义的术语与符号

| 术语 | 精确定义 |
|---|---|
| `D` | 缺损后残余实体骨组织；Native 输入为 \(\partial D\) 的 V1 面积采样 |
| `G` | 缺失实体骨块；目标为完整 \(\partial G\) |
| `E` | 缺失骨块的继承原始自由表面，不等同仅外板 |
| `J` | 缺失骨块与 D 共享的人工切除实体接触面 |
| `Q0` | 全局编码经 MLP 产生的原始 learned coarse/query 坐标 |
| `Q1` | 第一次 SCQ 更新后位置，\(Q^1=Q^0+\delta^0\) |
| `Q2` | 第二次 RF 更新后位置，\(Q^2=Q^1+\delta^1\) |
| `N0` | 以 Q0 为 query 在实际 256 Memory 中选出的 KNN8 索引 |
| `N1` | 以 Q1 为 query 重新选出的 KNN8 索引（仅 Requery） |
| `Static` | 第二头使用 N0，但相对几何仍以 Q1 计算；同容量对照 |
| `Requery` | 第二头使用 N1，且相对几何以 Q1 计算；主要候选 |
| `R/A/DAC` | DAC 旧报告的冻结权重 Requery/固定均值/方向组合反事实，不是 RIVE 的三模型训练 |
| `Native` | 无 GT 引导变换与后验模型选择的原始预测；GT 只用于评分 |
| `source` | 同一颅骨来源，关联五种缺损；推断与 bootstrap 的独立抽样单位 |
| `severe` | 旧研究定义 `E_P95>20mm OR J_Cover@2mm=0`，非医学安全标准 |

## 附录 B：正式结果报告的必要空表（均为未来待填）

### B1. 主要性能（严禁使用历史数据冒充 RIVE 新结果）

| train_seed | Fold | Static E_P95 | Requery E_P95 | ΔE | E 改善/退化来源 | Static J_P95 | Requery J_P95 | ΔJ Cover2 | Static severe | Requery severe | 新增/恢复 | 结论级别 |
|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---|---|
| 0 | C | 待运行 | 待运行 | 待运行 | 待运行 | 待运行 | 待运行 | 待运行 | 待运行 | 待运行 | 待运行 | 探索性配对 |
| 0 | D | 待运行 | 待运行 | 待运行 | 待运行 | 待运行 | 待运行 | 待运行 | 待运行 | 待运行 | 待运行 | 探索性配对 |
| 1 | C | 条件式 | 条件式 | 条件式 | 条件式 | 条件式 | 条件式 | 条件式 | 条件式 | 条件式 | 条件式 | 新 seed 重复 |
| 1 | D | 条件式 | 条件式 | 条件式 | 条件式 | 条件式 | 条件式 | 条件式 | 条件式 | 条件式 | 条件式 | 新 seed 重复 |

### B2. 关键机制反例（未来从 RIVE 实际快照填写）

| Fold/病例 | 类型 | Q0位置 | Q1位置 | Q2位置 | Dense位置 | E_P95 | J_P95 | J Cover2 | Pred→A2尾部 | N0/N1证据是否保存 | 是否曾参与假设形成 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| C/012 parietotemporal | 历史反馈放大 | 待运行 | 待运行 | 待运行 | 待运行 | 待运行 | 待运行 | 待运行 | 待运行 | 待确认 | 是 |
| D/069 random_2 | 历史覆盖不足 | 待运行 | 待运行 | 待运行 | 待运行 | 待运行 | 待运行 | 待运行 | 待运行 | 待确认 | 是 |
| 哈希固定对照 | 训练前预注册 | 待运行 | 待运行 | 待运行 | 待运行 | 待运行 | 待运行 | 待运行 | 待运行 | 待确认 | 否（需核对） |

**整份计划结束。RIVE 训练与评分尚未发生。**
