# Cranial-BCSP-FullMamba：SCQ-RF 空间重查询反馈与残差可靠性实验计划书

> **实验正式名称**：SCQ-RF（Spatial Re-query Feedback for Reliable Cranial Fragment Completion，面向颅骨缺失骨块可靠补全的空间重查询反馈）  
> **版本**：预注册实施草案 v1.0  
> **编制日期**：2026-11-14  
> **研究阶段**：SCQ B/S（2026-11-14）正式收束后的下一阶段；**本文件是拟执行协议，不是已实施实验，也没有获得任何新模型效果**  
> **模型约束**：保留 Attention-free Mamba Encoder–Decoder；允许 FPS、KNN、DGCNN/PointNet++、MLP、LayerNorm、归一化、几何与重建运算；**不引入 Transformer Self-/Cross-Attention**。  
> **任务约束**：以残缺颅骨骨组织完整边界 `∂D` 为输入，预测被移除骨块完整边界 `∂G=E_G∪J_G`；不将任务降格为原颅骨外表面补片。  
> **证据来源标记**：`[R]` 为用户上传的 SCQ B/S 正式报告；`[H]` 为此前 P0–P2、F0/LQI 研究的已提供记录；`[W]` 为截至本版日期通过公开网页核验的论文摘要、正式出版信息或开放正文；`[P]` 为**尚未验证的计划与推断**。严禁把 `[P]` 当作结果。

---

## 0. 执行摘要与唯一决策

**推荐的下一轮实验名称是 SCQ-RF，而非 SCQ-Gate、SCQ-Clamp 或“再加一个 Rim Loss”。**

SCQ B/S 的新候选 S 在相同训练设备、固定 SkullBreak BCSP V1、8192→8192、256 coarse、3900 steps、seed0 的合同下，较本轮重训的 LQI 基线 B 获得两折较广泛的平均收益：C/D 的 `E_P95` 从 `11.743→6.688`、`7.307→5.494 mm`，`J_Cover@2mm` 从 `38.77→49.88%`、`48.30→53.93%`；E 来源改善为 `15/21` 和 `18/21`，严重病例 `16→5`，但出现 **2 个新严重病例**，均在 C 折 frontoorbital。[R]

全队列更重要：S 的 **195/210** 例 `Qraw` 质心偏差超过 20 mm，且 **205/210** 例在 SCQ 后质心更接近 GT；E 退化的 65 例里仍有 **60 例**质心被拉近。这说明不能用 `Qraw` 偏位诊断“坏掉的 Query Head”，也不能凭位置改善认证形状正确。SCQ 的 `Qraw+δ` 可能已形成互相补偿的端到端表示，**不能统一 clamp δ，不能突然强监督 Qraw**。[R]

本阶段以**两个严格区分的研究问题**组织：

1. **归因问题（先做、不可跳过）**：S 的收益是否超出同样拥有局部特征、相同参数量与相同残差路径、但没有显式 7 维相对几何通道的 F 控制？F 尚未正式训练，不能说“显式几何本身已经获证实”。
2. **可靠性机制问题（仅在归因合同与零更新审计通过后）**：当第一次 SCQ 已把 `Qraw` 修正到 `Q1=Qraw+δ0` 后，**以 Q1 重新查询实际 Memory 近邻**，是否比继续沿用最初 Qraw 的近邻，更能纠正局部条件错配、降低新发严重几何失败，同时不牺牲 S 的 E/J 均值收益？

这一研究命名为 **SCQ-RF：空间重查询反馈**。其核心单因素不是“多一个 MLP”，而是**第二次残差校正时，Memory 邻域是否重新以修正后的 Query 位置检索**。设置同参数、同输入、同初始权重的 **RF-Static（固定旧近邻）** vs **RF-Requery（按 Q1 重查询）**，并将两者与同设备 S 比较。二者均不假设重查询必然正确：如果初始 Q1 仍在错误缺损区域，重查询可能放大错误，应由准入和开发集风险门证伪。[P]

**先后次序**：存档/合同 → F 容量归因 → RF 数学/数值与邻域可行性 → RF-Static/RF-Requery 同设备对照 → Native 全量评分与新发风险门 → 有条件的多 seed/独立确认。不要把这些步骤混成一次“堆模块训练”。

### 0.1 当前可以声称与禁止声称的内容

| 层级 | 当前可说 | 不能说 |
|---|---|---|
| 工程 | B/S 四模型按同设备、单 seed 配对训练并完成 Native 评分 [R] | F 已训练、RF 已训练或已通过科研门 |
| 几何 | S 两折 E/J、CD、覆盖的均值总体改善 [R] | 所有缺损、所有来源均改善；已达临床阈值 |
| 风险 | 严重数 16→5，恢复13、新发2 [R] | “没有灾难性退化”或“临床可靠” |
| 机制 | S 的残差经常将质心拉近；Qraw/δ 可能协同 [R+推断] | Qraw 一定坏；δ 过大必然错误；残差分工因果已经证明 |
| 显式几何 | S 组合结构有效 [R] | 7维相对几何独立贡献已证明（F 未训练） |
| 下一阶段 | RF 是明确可证伪的候选 [P] | 重查询一定修复 frontoorbital / 内外板 / Rim |

---

## 1. 任务定义、数据合同及冻结边界

### 1.1 几何与临床语义

原始实体骨组织 `C`、缺损后保留实体 `D`、被移除骨块 `G` 满足合成实体缺损的互补定义。模型任务为：

\[
\partial D \;\xrightarrow{\text{D-only model}}\; \partial G=E_G\cup J_G.
\]

- `∂D`：骨组织与背景交界的完整边界，可能包含外板、内板、孔洞/腔体边界、人工切除暴露壁和扫描视野截面。
- `E_G`：目标缺失骨块继承的原始未知表面，并不等于“只有颅骨外表面”。
- `J_G`：`G` 与 `D` 的接触切壁；其局部覆盖与整块补全必须同时报告。
- `∂G`：整块骨片完整边界，不是被删去的原始外表面 patch，不是实体/mesh 制造结果。
- 当前实体边界来自合成缺损的分割与冻结 voxel-face 参考；不是独立临床植入体精确 GT。不能把几何 P95 兑换为临床合格判定。[R,H]

### 1.2 数据和独立单位

| 属性 | 锁定内容 |
|---|---|
| 数据集 | 当前已开放 SkullBreak BCSP V1：84 来源、420 合成缺损，每来源五类 |
| 类别 | bilateral、frontoorbital、parietotemporal、random_1、random_2 |
| 每折训练 | 63 来源 / 315 病例 |
| 每折开发 | 21 来源 / 105 病例 |
| C/D | 开发来源互不重叠，但训练来源重叠；两折不是完全独立训练重复 |
| 输入/目标 | 8192/8192，固定 V1 exposed-face 物理面积采样 |
| coarse | 256；每个 coarse 生成32个 dense，共8192 |
| 坐标 | `c_D,s_D` 仅由输入 D 确定；G 共享 D 框架；评分回 world-mm |
| 开发结果性质 | C/D 已在 P1/P2/F0/LQI/SCQ 中多轮被观察，全部新结果**探索性** |
| 禁止触碰 | 未开放/受保护测试；新协议下仍封存的 confirmation20；不重新把早期已曝光的官方测试称为盲集 |
| SkullFix | 先前90来源已有 V1 几何 QC 与资产，但本阶段不直接当作独立确认；固定候选后另规划协议 |
| MUG500+ | 尚无获认证的高精度实体骨块 GT；不得引入为“提高样本量”的默认训练集 |

### 1.3 推理泄漏防护

在任何 `forward()`、KNN、序列化、动态邻域重查询、反馈门或候选选择中，都**不得访问** GT/G 的位置、目标中心、缺损类型标签、J/E 标签、GT bbox、Oracle ICP、病例风险标签。训练时 G 可进入既定监督；推理期新模块只能从 `D`、模型产生的 `Qraw/Q1`、编码 Memory `(S,F,z)` 计算。

不能依据开发病例的 GT 方向向量选择是否激活 RF；不能按 C/013、C/051 单独构造临床式阈值或手工“病例救援”。

---

## 2. SCQ B/S 报告的准确复盘：为什么这次不能再做质心和半径

### 2.1 正向证据

原冻结来源等权均值：

| 指标 | Fold C B | Fold C S | S−B | Fold D B | Fold D S | S−B |
|---|---:|---:|---:|---:|---:|---:|
| E P95 mm ↓ | 11.743 | 6.688 | −5.055 | 7.307 | 5.494 | −1.813 |
| J P95 mm ↓ | 14.983 | 9.202 | −5.781 | 10.669 | 7.948 | −2.720 |
| CD-L1 mm ↓ | 7.144 | 4.181 | −2.962 | 3.804 | 3.221 | −0.583 |
| E Cover@2mm ↑ | 55.08% | 63.83% | +8.75 pp | 64.19% | 68.20% | +4.00 pp |
| J Cover@2mm ↑ | 38.77% | 49.88% | +11.11 pp | 48.30% | 53.93% | +5.62 pp |
| Pred→A2 P95 mm ↓ | 13.598 | 10.440 | −3.158 | 9.726 | 9.451 | −0.275 |
| Pred→A2 >20mm 比例 ↓ | 7.80% | 4.19% | −3.60 pp | 2.31% | 1.76% | −0.55 pp |
| 质心误差 mm ↓ | 17.477 | 12.566 | −4.911 | 13.444 | 11.840 | −1.604 |
| 回转半径比 | 0.819 | 0.909 | 方向接近1 | 0.883 | 0.921 | 方向接近1 |

这些是**当前 B/S 配对重训**的数值，严禁与此前 F0/LQI 历史 checkpoint 的分数在不配对条件下替换比较。训练模型 S 新增693,507参数（约B的1.74%）。[R]

### 2.2 强负面证据：平均改善不能掩盖风险迁移

严重规则 `E_P95>20mm OR J_Cover@2mm==0`。C：B 11→S 3，恢复10、新发2；D：B 5→S 2，恢复3、新发0；合计 B16→S5，恢复13、新发2、共同严重3。[R]

固定高风险例（world-mm，**不能当无偏总体**）：

| 病例 | B→S E P95 | B→S J Cover2 | 诊断 |
|---|---:|---:|---|
| C/013 frontoorbital | 17.798→39.988 | 21.46%→0 | 新增严重；S 远端预测>20mm达99.73% |
| C/051 frontoorbital | 7.029→25.566 | 38.30%→2.48% | 新增严重；S 远端预测>20mm达80.90% |
| C/053 frontoorbital | 29.989→69.653 | 0→0 | 共同严重且恶化，不是新增 |
| D/046 parietotemporal | 43.838→56.968 | 0→0 | 共同严重且恶化，不是新增 |
| D/069 random_2 | 23.53→23.07 | 仍为严重 | 相对改善、绝对仍差；位置变近仍缺覆盖 |

frontoorbital 在 C 折 E/J 同时退化约3.967/3.886mm，在 D 折却改善4.031/4.322mm；不能归因于类别天生不适合 SCQ。[R]

### 2.3 全210例阶段归因：不能误读 Qraw

| 指标 | Fold C | Fold D |
|---|---:|---:|
| Qraw 质心距离中位 mm | 34.12 | 33.19 |
| Qused 质心距离中位 mm | 10.58 | 11.81 |
| Dense 质心距离中位 mm | 9.63 | 11.29 |
| SCQ使质心变近 | 102/105 | 103/105 |
| SCQ质心纠正量中位 mm | 21.77 | 20.06 |
| Dense进一步质心纠正量中位 mm | 1.01 | 0.63 |

总体195/210个 S 的 Qraw>20mm；改善145例里135例超过20mm，退化65例里60例超过20mm。**Qraw 大偏位对“之后好坏”的区分度很低**。因此本阶段**禁止**将 Qraw >20mm 作为推理校正门或训练专用“坏 Query”分类器；该标记只可用于离线描述。[R]

SCQ 的 coarse loss 实际监督 `Qused` 而非额外监督 `Qraw`，两者经过端到端训练后可能分工。突然加 `Qraw→GT` 强监督、把 δ 限制为几毫米、或以 GT 质心方向截断，会改变已获有效收益的表示合同。[R+推断]

### 2.4 下一步真正的未知量

- **因子 A：显式7维空间几何**是否独立有价值？当前只知道 S 相比 B 的组合收益；F 未训练。
- **因子 B：SCQ 的空间修正是否引用了真正有用的 Memory 邻域？** 对大幅 Qraw 偏移尤其值得检验；但不能提前判其近邻“必然错误”。
- **因子 C：某次残差方向偏差与形状覆盖缺失能否通过第二次 D-only 空间反馈纠正？** 这是本阶段 RF 假设。
- **因子 D：训练随机性/来源异质性**可否解释一部分正负结果？seed0 没有回答。

---

## 3. 对已有文献的核验与研究定位

### 3.1 按用户既有四级文献表组织，而非声称全部已精读

用户此前提供了颅骨修复、Mamba/点云补全、2025–2026 前沿补全和医学综述四组**论文题目清单**。清单是选题导航，**不是已经取得并精读全部全文的证明**。本章仅对已经通过公开期刊/会议页面或开放摘要核验的文章总结可确认事实，并将与本实验有关的推论另列。

### 3.2 高优先级近邻文献及其对 RF 的具体约束

| 文献 | 可核验内容 | 对 SCQ-RF 的设计约束 | 不允许的创新性主张 |
|---|---|---|---|
| [CompletionMamba, TIP 2025](https://doi.org/10.1109/TIP.2025.3597041) | Local SSM 使用欧氏邻域并注入 shape code | 不能把“局部 KNN+Mamba”当新颖点；RF关注**第一次补偿后重新查询同一输入 Memory 的受控反馈** | 不能宣称首个局部空间 Mamba [W] |
| [3DMambaComplete, 2024](https://arxiv.org/abs/2404.07106) | HyperPoint generation/spread 与形变重建，针对点云点集集中 | 必须同时量化范围收缩和全形状覆盖；避免只优化质心 | 不能宣称首次粗细渐进生成 [W] |
| [PointMamba, NeurIPS 2024](https://proceedings.neurips.cc/paper_files/paper/2024/hash/395371f778ebd4854b88521100af30ad-Abstract-Conference.html) | 空间填充曲线+Mamba主干用于点云分析 | 固定现有排序，不把本阶段改成多排序搜索 | 不声称SSM在点云首次使用 [W] |
| [Point Cloud Mamba, AAAI 2025](https://doi.org/10.1609/aaai.v39i10.33098) | Consistent Traverse Serialization 与位置提示 | 当前 RF 不依赖“换 XYZ 排序”才能发挥作用 | 不把坐标排序/提示作为原创 [W] |
| [DAPointMamba, AAAI 2026](https://doi.org/10.1609/aaai.v40i8.37596) | 跨域 patch 扫描与空间、通道对齐，强调序列化造成的拓扑破坏 | 反馈机制要独立报告空间条件与真实形状，不与跨域适配混为一谈 | 不能把“空间/patch 对齐”笼统宣称首创 [W] |
| [FusionMamba, Information Fusion 2026](https://doi.org/10.1016/j.inffus.2026.104378) | 空间感知聚合和 residual geometric Correction Module | **最直接的重合风险**：本研究必须通过反馈邻域的匹配消融，证明区别于泛化“几何残差校正” | 不能宣称首次 Mamba+几何残差修正 [W] |
| [BuildingComSSSM, 2026](https://doi.org/10.1016/j.jag.2026.105269) | Geometry-aware Mamba，但关键点生成含 self-attention、扩散含 cross-attention | 可作研究脉络，不可充当无注意力复现 | 不能把其公开结构称为纯Mamba [W] |
| [CDRMamba, BSPC 2025](https://doi.org/10.1016/j.bspc.2024.107376) | 颅颌面缺损修复使用3D U-Net与Mamba，针对影像分割/修复 | 医学相关，但任务表示和评价不同；不直接搬迁数值 | 不得称“首次将Mamba用于颅颌面修复” [W] |
| [SkullBreak/SkullFix, Data in Brief 2021](https://doi.org/10.1016/j.dib.2021.106902) | 数据集来源和合成缺损的官方定义 | 本研究公开来源子集不是官方全量数据；必须写实际84来源而非114+20全部 | 不把合成切除说成临床患者植入物 [W] |
| [Learnable Symmetry, CMPB 2025](https://doi.org/10.1016/j.cmpb.2025.108670) | 颅骨可学习对称性提升修复，存在不对称情形 | 对称是后续备选先验，**当前不加**；bilateral/额眶不能默认镜像可用 | 不宣称无先验的临床普适性 [W] |
| [Clinical Thickness/Rim, IJCARS 2024](https://doi.org/10.1007/s11548-024-03068-4) | 真实临床植入体的厚度和rim过渡与合成样本不同 | 现在只评价完整骨块 `∂G` 的几何代理，不加临床厚度/装配结论 | 不把2mm点覆盖等同临床接触 [W] |
| [MedPCFM, arXiv 2026](https://arxiv.org/abs/2606.24433) | PTv3确定性医疗点云补全与flow matching，含 SkullFix/SkullBreak | 后期应有同任务适配强基线；先核对输入/目标表示、splits、点数和指标 | 不跨协议直接排名 [W] |
| [Bayesian Skull Uncertainty, Scientific Reports 2026](https://doi.org/10.1038/s41598-026-54679-7) | 颅骨重建不适定，预测不确定性及厚度变异有价值 | 提醒“单一GT下低CD≠唯一解”；本阶段不声称已校准置信度 | 不将RF读出的响应包装为真实贝叶斯不确定性 [W] |
| [Revisiting Point Cloud Completion, ICCV 2025](https://doi.org/10.1109/ICCV51701.2025.02355) | 真实点云包含非均匀稀疏和丰富拓扑 | 保留未测真实临床泛化的边界；不把合成基准当临床 | 不宣称真实世界鲁棒性 [W] |

**研究定位**：[P] 本计划的差异化问题是：*在无Attention FullMamba与真实颅骨 BCSP 任务中，已被证实有用的大幅 `Qraw+δ0` 补偿之后，重新以修正位置向原输入 Memory 请求局部条件，能否在不破坏补偿的情况下改进困难病例可靠性？* 这仍需检索更全面的全文、代码和相邻领域的 re-query/refinement 工作才可形成最终 novelty statement；目前只是研究命题。

### 3.3 为什么不把2026前沿生成式补全立即加进来

PCDreamer、GenPC、SuperPC、RDS-Net、SymmFusion、计算感知 shape loss 等工作提示更强先验/形状损失路线，但当前阶段的任务是**把 SCQ 的新发整块失败从结构条件上解释与证伪**。同时改生成范式、采样、loss或对称性将失去本轮最重要的可归因性。保留为后续强基线/独立机制研究，不纳入本轮训练矩阵。[P]

---

## 4. 实验问题与可证伪假设

### 4.1 两个不同层级的研究问题

- **Q-F（归因）**：SCQ 的显式7维相对几何通道在同参数、同局部特征/同残差路径下是否提供增量收益？
- **Q-RF（可靠性）**：第二次纠正时依据 `Q1` 的实际新位置重新确定邻域，比沿用最初 `Qraw` 的邻域更有利于完整形状、接口与新发风险吗？

### 4.2 假设及其反例

**H-F**：`S−F` 在 E/J 和风险上的差异是显式7维空间几何特征的证据之一。**反例**：F 与 S 同等或更好；此时不能把S收益命名成“显式几何增益”，但可以把它保留为局部特征残差模型。

**H-RF（唯一新结构假设）**：`Q1=Qraw+δ0` 已包含有效的第一步补偿，重新查询实际 Memory 邻域可提供不同且有用的信息，从而降低**相对 S 的新增严重几何事件**，同时保持 E/J 表面质量。**反例**：RF-Requery 和 RF-Static 无差别、RF-Requery 更差、只是质心变好而 E/J 不好、或减少旧失败的同时制造更多新失败。

**H-阶段解释**：如果 RF 改善，`Q1` 邻域变动也许提供了新的条件；但只有匹配的 Static/Requery 消融才能把改善指向“邻域重选”。即使 Requery 优胜，也不证明故障一定来自原始邻域错误，更不能证明已经学到解剖对应。[P]

### 4.3 不开展的假设

- 不把所有新发灾难归咎于 Mamba 序列遗忘、coarse head 或FPS；这三种因果尚未识别。
- 不测试额外中心loss、半径loss、残差范数惩罚、直接 clamp、GT定向角损失、strong rim loss、对称约束或多轴重排序。
- 不以“后验找出了 C013 和 C051 的共同特征”直接设计部署门控。

---

## 5. 实验组、插入接口与分阶段训练矩阵

### 5.1 三个基础模型（前置 F 归因）

| 代号 | 结构 | 与 B 的差异 | 作用 |
|---|---|---|---|
| `B` | 2026-11-14同折重训 LQI，39,903,169参数 | 无 | 已完成的基础参照，不自动重训 |
| `S` | B + 原 SCQ（8邻居、局部均值/最大值、7维几何、残差） | +693,507参数 | 已完成的主要研究候选和 RF 母版 |
| `F` | 与 S 同结构同参数，7维显式相对几何以冻结特征投影替换 | 参数数与 S 相同 | **本轮尚未训练；第一道归因必需控制** |

**非常重要**：F 不是“没有任何空间关系”。F 的 KNN 邻域索引仍由实际 Qraw/S 坐标确定；它只移除**输入MLP的显式7维几何值**。若 F≈S，只能说明这7维几何的增量价值未获支持，不能宣称KNN/局部关系没用。[R]

### 5.2 两个 RF 机制模型（第二阶段，均保留S的完整第一步SCQ）

| 代号 | 第一次补偿 | 第二次校正头 | 第二次 KNN | 目的 |
|---|---|---|---|---|
| `S-ref` | 完全保留SCQ：`Q1=Qraw+δ0` | 无 | 无额外 | 同设备训练参考 |
| `RF-Static` | 相同 | 新增相同小MLP预测 `δ1` | 固定 `N0=KNN(S,Qraw)` 索引，以 Q1 重新计算相对几何 | 控制第二个MLP/额外学习容量的作用 |
| `RF-Requery` | 相同 | 与 RF-Static 完全相同 | 使用 `N1=KNN(S,Q1)`，以 Q1 重新计算相对几何 | **唯一拟验证的重查询作用** |

**主比较 `RF-Requery − RF-Static`；关键实用比较 `RF-Requery − S-ref`。** 不能只比 S-ref：若 RF-Requery 和 RF-Static 同幅改善，可能是额外校正容量而不是重查询产生收益。

### 5.3 执行顺序与预算上限（绝非自动授权）

**条件A：原 S 训练GPU/驱动/镜像与所有冻结数据均可复核且相同。** 先训练 `F_C,F_D`（2个run），同折对照当前 S；若 RF 获准，再训练 `RF-Static_C/D`、`RF-Requery_C/D`（4个run）。旧 S 仍用于复查，但单seed统计局限不变。

**条件B：训练资源已更换，不能严格恢复原环境。** 先在新环境同设备匹配重新从头训练 `S'_C/S'_D` 与 `F_C/F_D`（4个run），再在相同冻结环境、相同初始化与批次合同下训练 RF-Static 和 RF-Requery（4个run）；**建议最多8个新完整训练**。`S'` 是该环境下所有新机制的有效参考，不用历史 S 减少配对成本后又声称同设备归因。

| 阶段 | 输入条件 | 新完整训练数量 | 产物/门槛 |
|---|---|---:|---|
| A0 身份与归档 | 原 B/S 的源码、checkpoint、预测、评分、输入身份可确认 | 0 | 能精确恢复S路径；若失败先停止 |
| A1 F前置 | 环境A：F×C/D；环境B：S'及F×C/D | 2或4 | S/F明确归因结果；保留全部病例 |
| A2 RF静态分析/合同 | S完整Qraw/Q1、实际Memory `(S,F,z)` 可获得 | 0完整训练；必要时有限有授权forward | 邻域确实可变化，数值/泄漏检查通过 |
| A3 RF人工准入 | RF-Static/Requery CPU/P3 与CUDA零更新 | 0完整训练 | 前后向、batch8、显存与状态合同 |
| A4 RF正式比较 | 同fold、同环境、同顺序 | 4 | 新的Native全量两折及风险转移 |
| A5 确认 | A4确有跨折收益且风险门通过 | 视新预注册另定 | 多seed、独立来源，不属于A4已完成 |

不能在 A1 的 Fold C 看到不利结果后修改 F 或 S' 的 Fold D 训练设置；不能在 A4 的 C 折看到失败后临时改 KNN k、头宽度或δ尺度以“救 D”。

---

## 6. 原 SCQ 公式与 RF 的唯一新结构公式

### 6.1 必须完整复用的 SCQ 母版合同 [R]

记 `Memory` 坐标 `S∈R^{256×3}`、特征 `F∈R^{256×384}`、全局 `z∈R^{1024}`、原 learned query `Qraw∈R^{256×3}`，每个query取 `k=8`：

\[
N_i^{(0)}=\operatorname{KNN}_8(S,Q_i^{raw}),\qquad d_{ij}^{(0)}=S_j-Q_i^{raw}.
\]

Memory 特征**逐token**用无仿射 LN (ε=10⁻⁵)，在邻域求 `mean/max`。相对几何：

\[
\mu_i^{(0)}=\operatorname{mean}_{j\in N_i^{(0)}} d_{ij}^{(0)},
\quad \sigma_i^{(0)}=\sqrt{\operatorname{mean}_{j\in N_i^{(0)}}(d_{ij}^{(0)}-\mu_i^{(0)})^2+10^{-6}},
\quad \rho_i^{(0)}=\operatorname{mean}_{j\in N_i^{(0)}}\lVert d_{ij}^{(0)}\rVert_2.
\]

`g_i^(0)=[μ(3),σ(3),ρ(1)]` 共7维。构造 `h_i^(0)=[z(1024), f_avg(384), f_max(384), Qraw_i(3), g_i(7)]`，总 **1802维**：

\[
\delta_i^{(0)}=W_2\operatorname{GELU}(W_1h_i^{(0)}+b_1)+b_2,
\quad W_1:\;1802\to384,
\quad W_2:\;384\to3,
\quad Q_i^{(1)}=Q_i^{raw}+\delta_i^{(0)}.
\]

原 `W2,b2` 零初始化；其余参数、GELU精确实现、排序、已冻结loss均保持原报告合同。`Q1` 即原 `Qused`。不对 `Qraw` 另加独立GT监督；旧损失继续通过 `Qused` 与最终Dense传播。[R]

### 6.2 RF 唯一新增操作 [P]

**目标：保留第一步大幅有效补偿，只改变第二次校正时被读取的真实 Memory 邻居。**

设 `A ∈ {Static, Requery}`，第二次邻域按以下两种方式生成：

\[
N_i^{Static}=N_i^{(0)},\qquad
N_i^{Requery}=\operatorname{KNN}_8(S,Q_i^{(1)}).
\]

两组都**在 Q1 的当前坐标系**下计算二次相对几何，确保唯一的索引差异：

\[
d_{ij}^{A}=S_j-Q_i^{(1)},\quad
f_{avg,i}^{A}=\operatorname{mean}_{j\in N_i^A}\operatorname{LN}(F_j),\quad
f_{max,i}^{A}=\max_{j\in N_i^A}\operatorname{LN}(F_j).
\]

\[
\mu_i^A=\operatorname{mean}_{j\in N_i^A}d_{ij}^A,
\quad\sigma_i^A=\sqrt{\operatorname{mean}_{j\in N_i^A}(d_{ij}^A-\mu_i^A)^2+10^{-6}},
\quad\rho_i^A=\operatorname{mean}_{j\in N_i^A}\lVert d_{ij}^A\rVert_2,
\quad g_i^A=[\mu_i^A,\sigma_i^A,\rho_i^A].
\]

\[
h_i^A=[z,f_{avg,i}^A,f_{max,i}^A,Q_i^{(1)},g_i^A]\in\mathbb R^{1802},
\quad \delta_i^{(1),A}=V_2\operatorname{GELU}(V_1h_i^A+c_1)+c_2,
\quad Q_i^{(2),A}=Q_i^{(1)}+\delta_i^{(1),A}.
\]

固定**第二次校正头** `1802→128→3`，其参数数预计为 `1802×128+128+128×3+3=231,171`（不含实现中其他意外新增项；实施时必须原生程序数参核验）。`V2,c2` 零初始化，保证新模型在初始 forward 下与S输出相同；第一步SCQ头的初始化和参数完全照旧。

`Q2` **一致替代下游全部 Qused 消费者**：Query feature、q_pos、排序、LQI self/conditional KNN、256 coarse Chamfer监督、dense中心与FC重建。不能只把 Q2 写日志或只改最终的坐标加法。

**主变量定义必须严格**：Static 与 Requery 共享同样的 `h` 定义、LN、MLP、参数量、初始化、损失、KNN k=8、训练顺序；**唯一**不同是第二次读取 Memory 的邻域索引使用 Qraw 时的 `N0`，还是 Q1 时的 `N1`。在 Static 中相对距离也按 Q1 更新，防止“是否使用新坐标”混杂进“是否重查询”。

### 6.3 为什么不加置信门或强制截断？

`Q1` 由原SCQ给出，报告显示中位约20mm的质心纠正有价值。统一给 `δ0` 或 `δ1` 设小界限，可能损坏大多数正确病例。因此本轮**不采用** sigmoid gate、阈值 fallback、按GT风险开启的开关、额外方向 loss 或固定残差半径；仅测试“在修正位置重查询”是否能改善。所谓“可靠性”在本阶段是**病例级测量目标**，不是已训练可校准的概率或分支 confidence。[P]

### 6.4 对重查询方案自身的限制

1. KNN 查询点 `Q1` 可能处于空缺实体内部，与残余骨表面存在真实空间间隔，**邻居远不等于错误**；不能用距离5mm/10mm这类任意阈值自动拒绝。
2. 如果 Q1 指向完全错误的头骨区域，重新查询也可能收集错误特征，不能预言它会修复 C013/C051。
3. 静态/动态 KNN 索引不可微；被索引 Memory 特征与显式距离向量仍可传梯度，**不能把 KNN argmin 写成有梯度的操作**。
4. 二次头有额外参数；Static vs Requery 匹配容量解决这一比较的主要混杂，仍需 S-ref 判断新增反馈是否整体划算。
5. 对称性、解剖厚度、层间拓扑没有被本公式显式约束；即使改善位置，不代表形状结构正确。
6. 第二步更新引入新的查询-邻域反馈回路，存在训练适应和错位反馈，必须保存 Qraw/Q1/Q2/P 四阶段来验证，而不能只看最终P。

---

## 7. 内存与数值实现约束

### 7.1 源码接入点与接口

**单一新位置**：`Q1 = original_SCQ(Qraw,F,S,z)` 之后、原 LQI Decoder 接受 Query 之前。旧 Encoder、原 SCQ、LQI 的双向/条件 Mamba、局部图、原 reconstruction head 保持。禁止为 RF 临时实现 Cross-Attention。

建议在模型输出/trace中明确区分：

```text
memory_xyz [B,256,3]      memory_features [B,256,384]
z [B,1024]                q_raw [B,256,3]
delta0 [B,256,3]          q1 [B,256,3]         # original SCQ Qused
idx0 [B,256,8]            idx1 [B,256,8]
delta1 [B,256,3]          q2 [B,256,3]         # new decoder-used coarse
p_dense [B,8192,3]
```

对 `S-ref` 只能宣称原路径中 Q1 与 P 已有；不能假定历史 `F`/Memory、idx0/idx1 的完整张量已在210例预测档案中。新局部诊断若需补取，必须在身份复核后有限授权 forward，保存实际真实 Memory 对应关系。

### 7.2 KNN与张量顺序一致性

- 邻居必须在**实际 256 memory token** 中检索，不能用8192原始输入点替代。
- 不得混用 world-mm Q 与 normalized memory S；二者都在同一 D-only 归一化坐标进行KNN。
- Stable XYZ sort/unsort 按原 LQI frozen contract，任何原始索引tie-break要一致。
- 每层 LQI 的 self/conditional KNN 对最终 `Q2` 重新确定，不能仍悄悄沿用 `Q1` 索引。
- `Static` 只重用第二次校正模块的 `N0`，不等于下游 LQI 一律冻结其KNN。
- 输入归一化、GT mask、A1/A2评测参考绝不通过新增模块传入。

### 7.3 推荐伪代码（逻辑规格，不代表已核验源码）

```python
memory_xyz, memory_feat, z = encode_D_only(partial)
q_raw = learned_coarse_head(z)
idx0 = knn(memory_xyz, q_raw, k=8)
delta0 = original_scq_head(z, memory_xyz, memory_feat, q_raw, idx0)
q1 = q_raw + delta0

if mode == 'rf_static':
    idx_feedback = idx0  # index selection based on original q_raw
elif mode == 'rf_requery':
    idx_feedback = knn(memory_xyz, q1, k=8)
else:
    raise ValueError('unsupported mode')

# NOTE: geometry is Q1-relative in BOTH modes
feedback_features = build_scq_features(
    z=z, memory_xyz=memory_xyz, memory_feat=memory_feat,
    query_xyz=q1, neighbors=idx_feedback
)
delta1 = zero_output_initialized_feedback_mlp(feedback_features)
q2 = q1 + delta1
p_dense = original_attention_free_lqi_decoder_and_head(
    memory_xyz, memory_feat, z, query_xyz=q2
)
loss = chamfer(q2, gt8192) + chamfer(p_dense, gt8192)
```

必须核对原 `get_loss()` 具体使用 `coarse=Q2`，以及 backward 到原 `Qraw/δ0` 的路径。**不可**因为旧训练日志 `loss_sparse=0` 就误以为 coarse 无监督——它对应关掉的 denoise，重建loss含 coarse+fine。[R]

---

## 8. 零训练预检：先确认重查询有可检验的信息差异

### 8.1 必要材料

- 原 S 的 checkpoint、源码与依赖签名；固定D-only输入和fold/source映射；归一化 metadata。
- **从当前权重真实 forward 得到** Memory `(S,F,z)`、`Qraw/Q1`。若历史归档缺 Memory，需限定计算预算并明确申请，不以估算FPS代替实际 token。
- 冻结原 S/B 开发预测与评分文件；失败病例 C013、C051、C053、D046 和反例 D069 只作诊断，不重新定义模型选择人群。

### 8.2 只读/有限新forward检查

| 编号 | 核验项 | 目的 | 停止条件 |
|---|---|---|---|
| D0 | Memory/Qraw/Q1身份、坐标、有限值、batch shape | 排除张量配对错误 | 任何错源/错坐标/非有限即停 |
| D1 | 每个Query `|N0∩N1|/8`、邻居替换比例及其来源分布 | 量化是否存在实际邻域变化 | 全部近乎相同则机制无区分度，先不训练 |
| D2 | 新旧邻居到Q1的物理距离分布、邻域特征差异（不以GT筛选） | 检查是否只是索引变化、特征不变 | 近乎无特征差异则不强推本假设 |
| D3 | C013/C051及固定正常/明显改善例的变化和分布 | 确认边界、极端与常见例并存 | 不准仅凭两失败例选择结构参数 |
| D4 | Static/Requery 初始zero-output一致 | 确认新头中性与唯一索引差异 | 非零初始预测差必须停 |
| D5 | 无GT辅助的 D-only 条件来源审计 | 防泄漏 | 使用GT bbox/centroid/J则禁止训练 |

D1/D2 的“有差异”是**进入证伪训练的必要但非充分条件**，不是性能通行证。不设事后挑选的“5mm正确邻域”阈值；以数值可分性、可复核性和实现正确性为准。未核验全210例时，应明确局部样本数量及被选择方式。

### 8.3 关键数学反例（必须通过CPU/P3）

1. `δ0=0` 时，`Q1=Qraw`，则在确定性 KNN tie-break 下 `N1=N0`，两个反馈模式输出应一致。
2. `Q1≠Qraw` 但邻居索引恰好没变时，Static/Requery 构造的 `h` 应完全相同。
3. 邻居发生变化时，两个反馈模式只因取邻居不同产生 `h` 差异，不因相对中心选择不同产生差异。
4. 旋转/平移改变坐标的一般情况下模型**不承诺旋转不变性**；不能将对坐标变换的响应称为bug，除非违反已冻结归一化/排序合同。
5. zero-output `V2=c2=0` 时 `Q2=Q1` 且最终 P 必须与原S路径在同一模型初始状态一致；初始step的反馈头第一层梯度可为零，最后一层应有非零有效梯度。
6. 梯度通过 `Q1` 的显式距离计算传递，但不穿过KNN整数索引；不得错误声称邻域选择可微。
7. B=1、B=8 下 batch独立、张量形状/精度/有限性一致；重复调用禁用随机增广时结果落在事前数值容差内。

---

## 9. CPU、CUDA与工程准入（只测新增路径）

### 9.1 CPU实施检查

- 参数量由实际模型打印核验：`RF-Static == RF-Requery`，新增反馈MLP数量符合规格。
- 恢复每个原S模块与参数组，不允许遗漏 Mamba `A_log/D` 的 no-decay 例外。
- 同fold两模型共有参数初始值按name/shape/dtype及持久状态核对；新反馈头使用隔离随机流，种子和全初态指纹一致。
- 全量禁止的 Attention 模块/dispatch守卫只限定本次冻结执行路径，不宣称审计了不可见第三方二进制内部。
- Forward 形状、inference D-only、归一化、Q2全路径消费、loss一次计入及有限反向梯度。
- 已有P3的核心通道可复用，不扩建与本假设无关的通用文件/权限框架。

### 9.2 真实 CUDA 零更新准入

建议固定少量人工样本，分别执行 Static/Requery：eval(batch1) forward + loss + backward，train(batch8) forward + loss + backward，**0 optimizer step**；不做 BNCal/模型训练。记录真实后端 native Mamba、PointNet2、PyTorch `cdist`、BN状态恢复、Torch allocated/reserved、SMI、RSS、CUDA峰值；一旦资源超预算/非有限，立即停。

特别检查：新增的两次 256×256 KNN邻域运算虽小，但不能从理论上推断全网提速或显存低于历史S；实际 batch8 内存应满足原20GiB Torch和22,528MiB设备的限制。

### 9.3 原训练数值政策不可偷换

- Python/PyTorch/Mamba/PointNet2 provider、CUDA、Chamfer路径以可恢复环境为准。若版本变化，必须显式披露，不能称完全相同合同。
- FP32；TF32=false；不自行切换AMP、编译新Chamfer、升级torch后再与历史数值横向作严格因果比较。
- 原生Mamba backward有限非位级确定性照实报告；通过局部审计不保证所有3900步bitwise一致。
- 原工程故障与模型科学负结果分别保留；不自动重试掩盖失败。

---

## 10. 正式训练合同与来源统计

### 10.1 与 SCQ B/S 配对的完整合同

| 项目 | 锁定值 |
|---|---|
| 每run | fold C 或 D；训练seed0；100个traversals |
| 每fold训练/开发 | 315/105病例；63/21来源 |
| batch | 8，drop_last；每遍历39步 |
| 总更新/曝光 | 3900更新、31,200训练曝光、300 drop事件 |
| optimizer | AdamW lr1e−4、betas(0.9,0.999)、eps1e−8，clip10 |
| 有效weight decay | 常规矩阵5e−4；bias/1D/SSM例外0 |
| LR | `1e-4 * max(0.9**(epoch/21), 0.02)` |
| BN | `max(0.9*0.5**(epoch/21), 0.01)` |
| loss | **原 coarse CD(Q2,G)+dense CD(P,G)**；denoise/off；H1/H2/rim/法向/off |
| dtype | FP32, TF32=false；相同冻结 Mamba 后端政策 |
| model selection | 固定最后epoch99、step3900 checkpoint；不按dev挑epoch |
| 必须配对 | 同fold初始化、实际病例/来源顺序、LR、BN、GT8192和D-only输入 |
| 禁止 | TTA、GT ICP、train内 dev挑选、resume、自动改权重、重建缺损、换采样 |

新增 F、Static/Requery 的种子原则应先写入配置并冻结，不能一看到单折结果就改变第二折种子或drop顺序。

### 10.2 训练与推理数据身份

- 每个 source_id 的5类缺损都属于同一统计聚类单位。
- 开发折 C/D 的train有重叠；同一来源不能出现同折train/dev混合。
- 数据 checksum、V1采样seed与稳定前缀、D-only center/scale、GT8192、A1/A2参考指纹固定。
- S/F/RF 在同折不得因模型有不同forward次数而换用不同随机增广/GT采样；严格记录实际随机流。
- 保护集不触碰；多次开发集探索不记作独立确认。

---

## 11. Native评价指标与几何对象

### 11.1 主要评价

**主终点** `E_P95`：A1物理面积加权的参考 E→Pred 最近邻距离 95分位，病例先算、每来源5缺损均值、每折21来源等权。单位world-mm。不得使用把全部点拼接后整体P95替换。

必要协同指标：`J_P95`、`E/J Cover@0.5/1/2mm`、`CD-L1`（未平方双向欧氏最近邻均值的半和）、`Pred→A2 P95`、`Pred→A2 >20mm预测比例`、质心误差、回转半径比、P95分布尾部。A1/A2与MC-B参考保持冻结，不改变2mm或20mm作为临床阈值的解释。[R]

### 11.2 风险与配对转移

严格沿用：

```text
severe_geometry = (E_P95 > 20 mm) OR (J_Cover2 == 0)
placement_tail = (dense_centroid_offset > 20 mm)
compact_distribution = (dense_radius_ratio < 0.9)
```

同时记录 `baseline_severe`、`candidate_severe`、`new_severe`、`recovered`、`shared_severe`。S本轮为5/210严重，但下一实验相对**重新匹配的 S-ref**统计。不能仅凭 `S严重5→RF严重4` 说安全，因为可能新增了其他4例且恢复了5例。

### 11.3 全量中间层诊断（本轮为必要产物）

对每个模型/病例保存并汇总（可分别归档大张量与轻量表）：

- `Qraw`、`δ0`、`Q1`、`δ1`、`Q2`、`P`：每阶段质心误差、半径比、均值/分位点位移（世界mm）。
- `N0,N1`邻域重合率、新旧邻域的实际3D距离分布、对应的Memory feature差别（无GT推理侧可计算）。
- 对每一来源与缺损类型关联：E/J P95、覆盖率、CD、逆向离群与风险转移。
- 重点反例：`质心改善但E/J退化`、`无预测>20mm远端点但E严重漏覆盖`、`J Cover为0但E_P95未>20`、`大片点团移出目标区`。
- 对 Q1→Q2 的残差方向余弦，只有离线评分阶段可使用GT求方向；禁止把GT方向余弦反馈到推理。

不能将 `Qraw` 与 `Q2` 看成同一模型关掉SCQ的完整预测；模型共享训练后会对新模块适应，反事实关闭需要额外同权重forward，不能通过日志推演。

---

## 12. 统计设计、重复性与推断边界

### 12.1 配对统计对象

主要单位为 **42个已开发来源**，按Fold分别呈现21个来源的成对差值；5个缺损为来源内相关观测。对每折、各指标：均值差、来源中位差、改善/退化来源数、最差五来源、IQR、风险转移矩阵。

应将 source-bootstrap 程序、迭代数、随机种子、重采样单位、单双侧区间及目标比较**在看新数据之前冻结**。建议探索性使用每折来源级配对 bootstrap（如10,000次，95% percentile或BCa二者预先选定一种），但因42来源和已反复观察的开发集，区间只描述采样不确定性，**不是多seed或独立测试证据**。跨Fold训练重叠时不要把两折bootstrap当完全独立研究重复。

多指标避免未经调整的大量显著性陈述；当前主比较预注册为 RF-Requery−RF-Static 的 E_P95与新增严重风险，并同时报告 RF-Requery−S-ref、J Cover2及反向尾部。来源bootstrap若区间包含零，应表述为估计不精确。

### 12.2 为什么还需要多seed

同一GPU、同初始化/batch顺序提高可比性，但 Mamba 的有限梯度非位级确定性和模型训练本身会造成轨迹差异。单seed的折间一致不是“多随机性稳定”。若首轮有可保留收益，再至少登记两个额外seed，进行同seed成对 baseline vs candidate、同设备时序控制；必要时分开报告训练种子波动与采样seed波动。**不是把同来源五类缺损视为五次独立实验。**

### 12.3 独立确认集

探索阶段结束后固定公式、版本、seed策略和模型选择准则，才打开受保护的、未在本协议下用于开发的来源。此前ordering早期使用过官方test，不能重新给它“完全未暴露”身份。若使用SkullFix，需先锁定其独立80/10任务适配/开发规则，明确SkullFix与SkullBreak分布及GT语义差异，不能称临床真实植入体外部认证。MUG500+仍不作默认精确GT。[H]

---

## 13. 门槛、失败模式与预注册停止规则

### 13.1 Gate R0：合同可恢复

- **通过条件**：旧B/S的主要源码、checkpoint、S的训练和预测身份可复核，F定义与报告一致；输入/目标/参考和模型接口一致。
- **失败处理**：暂停全部新训练，先恢复与保存研究资产；不得用不同版LQI/F0历史分数充当本轮S。

### 13.2 Gate R1：F归因

- **通过含义**：得出可复核的S vs F比较，不意味着必须S胜出；明确显式7维几何的证据级别。
- 若 F≈S 或 F优于S：停止将当前SCQ收益宣传为“显式7维几何”贡献；可以继续研究反馈，但论文方向应调整为局部条件残差反馈，而非“几何通道是关键”。
- 若 S明显优于F：可支持显式几何在**这套模型**中的增量价值，但仍需要多seed/独立数据与其他容量对照才可形成最终结论。
- F如果出现更多新发严重病例也要如实报告，不只挑E均值。

### 13.3 Gate R2：RF实现和可区分性

- Static/Requery相同参数量和初始化、loss、原S权重随机流。
- `Q1=Qraw` 反例下二者严格一致；KNN变化来自真实Memory而非错源、排序或GT。
- `Q2`进入完整LQI及coarse loss；无新的Transformer attention；FP32、batch8可执行。
- 如 N1 与 N0 始终不变或其条件张量无有意义差异，本假设**缺乏可区分机制**，应停止而非凑训练结果。
- 非有限梯度、资源超限、loss/数据泄漏或状态恢复失败即停。

### 13.4 Gate R3：探索性可靠性晋级（严格目标；非临床标准）

为了避免事后为模型设置宽松阈值，本计划提出一个**明示较严格的探索性研究目标**，应在第一轮新训练前正式签入静态配置：

1. **新发严重**：在两折全部210例中，相对匹配 S-ref，`RF-Requery` **不新增严重几何病例**；并至少恢复一例S-ref现有严重病例。若出现新发，不能宣称“可靠性获得改善”，即使净数下降。
2. **完整形状**：`RF-Requery−S-ref` 的来源等权 E_P95 在 **两折都不变差**（允许精确相等）；`RF-Requery−RF-Static` 两折同向不劣，至少一折有改善。不要靠单个异常病例的巨大改善掩盖另一折来源层普遍退化。
3. **接口**：J Cover@2mm 在两折相对 S-ref 不下降；J_P95、E_Cover2、CD及预测→A2远端离群完整披露。
4. **风险长尾**：placement_tail、compact_distribution 及预测远端>20mm比例不能出现新的系统性恶化；重点报告C折 frontoorbital 和已知五个固定困难例，但不得忽略其他类别。
5. **机制增量**：若 RF-Requery≈RF-Static，不得把任何共同改善归因于重查询；若Static更好，应停止Requery路线。

**关于严格门槛**：上述是可证伪的研发晋级门，不是医学标准，也不表示此前S已达到该级别。在单seed探索阶段，“零新发”仍可能偶然，只有多seed与独立确认能谈稳健性；若候选未达到，完整报告负结果，**不得结果后放宽 R3**。

### 13.5 失败分支的科学处理

| 观察 | 合理下一步 | 不允许做法 |
|---|---|---|
| F≈S | 显式几何贡献暂不成立，重新定位模块机制 | 继续写“几何是增益根因” |
| Requery≈Static | 额外反馈MLP可能有收益，但动态重查询独立价值不足 | 增加k/多尺度/SSM使原假设不可证伪 |
| Requery比Static差 | 记录邻域变化、位置错配和失败病例；停止该候选 | 只删除坏病例证明成功 |
| 质心大幅改善但E/J退化 | 用形状/覆盖/反向距离归因，停止“只看位置” | 再加质心loss或clamp救结果 |
| E均值改善但新增严重病例 | 不能晋级可靠性；把风险事件列为主要负结果 | 报净减少掩盖新发 |
| C好D差 | 结论混合，保留fold及类型分层，不调D救模型 | 重新种子直到D改善后声称稳定 |
| 性能好但GPU/驱动不配对 | 严格结构因果仍待配对复现 | 把跨设备耗时/差值做正式因果 |
| RF完全失败 | 停止错误局部锚点反馈路线，考虑**独立D-only粗位置提案**作为下一轮另立假设 | 本轮悄悄增加全局定位器/对称模块 |

---

## 14. 与论文创新点的距离：哪些可以写，哪些还不能写

### 14.1 目前的论文级表述（可用但必须限定）

“在合成颅骨实体缺损的完整骨组织边界点云任务中，我们建立了无 Transformer Attention 的 FullMamba 基线。初步开发实验表明，输入 Memory 的局部特征及相对几何参与 coarse Query 残差，可在两个开发折改善完整自由表面及接触切壁指标，但存在新发严重失败。我们进一步研究补偿后重查询条件能否提高反馈可靠性。”

最后一句目前是**研究计划**，不可写成已做完结果。即使新RF成功，也不能在未完成相关全文核对与强基线比较前声称首次提出“多次KNN refine”或“唯一的几何修正”。

### 14.2 与 FusionMamba/CompletionMamba 的差异需要实证维护

- CompletionMamba 已有欧氏邻域Local SSM与shape-aware模块；“有KNN+Mamba”毫无新颖性保证。
- FusionMamba 已有空间感知全局融合及residual geometry Correction Module；“有空间补偿”也不是新颖性保证。
- 本轮可争取的具体差异是**多阶段coarse补偿后，针对实际修正位置重查询残颅Memory，且通过静态近邻同容量对照验证**；前提是确认没有已有相同设计，且Native几何/可靠性真正获益。[P]
- 如果它仅在一个seed开发数据上有益而风险未降低，适合成为机制负结果/消融，不适合作为论文主要创新。

### 14.3 保留第二项创新空间，但不在同一轮实施

若RF能稳定生成完整骨块，后续可单独研究`E_G/J_G`几何分区、内外板/共享切壁一致性和高保真细化；当前只保留测量而不加新loss。基于临床implant厚度/rim研究，未来仍须将合成实体骨块与制造形态分开，避免直接把 `∂G` 当成临床最终implant。[W,H]

---

## 15. 产物与归档、复现合同

### 15.1 不可覆盖原件

本阶段所有新文件写入新版本命名空间，旧2026-11-14 B/S的训练、score、prediction、H1/H2/F0/LQI历史证据均只读。旧S/F0/LQI及当前S正式ckpt必须及时做长期备份；报告只列哈希不等于完成备份。

建议目录结构（示意，路径不代表当前已存在）：

```text
experiments/cranial_bcsp_fullmamba_scq_rf_20261114/
  00_protocol/
    frozen_hypothesis.md
    configs_C_D.json
    data_model_reference_hashes.json
    gates_and_stats.json
  01_attribution_F/
    cpu_checks/
    paired_training/{fold_C,fold_D}/
    native_predictions/
    native_scores/
  02_memory_requery_diagnostic/
    paired_inputs_and_memory/
    neighbor_overlap_summary.csv
    numerical_contract_tests.json
  03_rf_static_requery/
    implementation_and_identity/
    cpu_p3/
    cuda_zero_step/
    training/{static_C,static_D,requery_C,requery_D}/
    native_predictions/
    native_scores/
  04_full_queue_mechanism/
    case_and_source_metrics.csv
    severe_transitions.csv
    qraw_q1_q2_dense_diagnostics.csv
    per_type_summary.csv
    fixed_case_visualizations/
  05_decision/
    gate_decision.json
    limitations_and_next_step.md
    reproducibility_manifest.json
```

### 15.2 每run必须保留

- SHA256：源码提交/文件、数据清单、有效配置、初始化/持久state、checkpoint、预测归档、评分实现、最终CSV/JSON。
- 精确实训：3900步的实际批次/source顺序、LR/BN、loss、梯度有限性、曝光与drop。
- 资源记录：GPU UUID/驱动、Mamba/torch/provider版本、峰值显存/RSS、退出码、失败attempt及修复原因。
- 同fold所有开发病例的 Native 原预测；禁止基于表面误差删点、做ICP、TTA、择优实例。
- B/F/S/Static/Requery 对照必须能追溯“哪个阶段复用冻结权重、哪个阶段重新从头训练”，避免模型历史版本混淆。
- 不保存随机人名或患者身份到公开输出；按source ID管理研究来源。

### 15.3 不可替代的人工检查清单

- [ ] 原B/S报告的指标、严重病例与source折表可用原冻结标量逐项复核。
- [ ] F 的“固定特征投影”的真实实现与报告一致，参数量与S相同。
- [ ] RF两臂只在第二次KNN索引不同，且N0/N1使用真实256Memory。
- [ ] 两次反馈头同初值、零输出、完整下游Q2接口正确。
- [ ] 新结果无GT推理泄漏，无受保护来源访问。
- [ ] GPU/驱动比较是同设备、同fold、同初始化与病例顺序；不同须列为混杂。
- [ ] 主指标E、J、CD、双向覆盖、远端离群及新发严重全部报告。
- [ ] 来源聚类统计与多seed证据分别标注，不将210病例当210独立患者。
- [ ] 阶段阴性结果如实收束，不为追求论文正结果事后加模块或重选source。

---

## 16. 最小执行顺序与组会决策问题

**第1步：资产与归因。** 盘点B/S保存状态；决定是否能恢复原GPU。通过F正式同容量训练，先回答显式几何通道的独立价值——这是SCQ论文创新性最基础的因果归因缺口。

**第2步：唯一机制的可行性。** 用真实S权重读取小范围Memory与Qraw/Q1，核验在Q1处重查询确实能产生不同的实际输入条件；Static/Requery计算图与公式预注册，CPU/P3+人工CUDA零更新准入。

**第3步：两折同设备结构对照。** 使用匹配的S-ref、RF-Static、RF-Requery；主要检验**动态重查询是否额外降低严重失败且不损失E/J**。保留Qraw/Q1/Q2/P全流程，来源等权和完整风险转移。

**第4步：硬停或晋级。** 如重查询无独立收益或制造新严重失败，收束为负结果，下一轮另立不依赖错位Query的D-only粗位置提案研究；若获得明确收益，再冻结模型开展多seed和未反复开发来源确认，之后才研究切壁高保真与临床厚度。

组会需要作出而不应留待新结果后决定的选择：

1. 原 S 训练GPU是否可恢复？若不可，则应重训同环境 S' 以避免 F/RF 跨设备混杂。
2. 是否同意将“F归因”列为必经步骤？若不同意，则论文不得声称显式7维几何对收益具有独立贡献。
3. 是否同意RF主比较必须为 **Requery−Static** 而非仅 Requery−S？
4. 是否同意“相对S新增任何严重病例即不能晋级可靠性”作为本次严格研发门？
5. 本轮可授权完整训练的最大数量（环境A建议≤6，环境B建议≤8）；超出必须另立研究问题而非自动延长预算。

---

## 17. 结论

**下一阶段不应再将研究问题简化成“coarse质心错误所以加中心loss”或“δ很大所以把它缩小”。** 用户提供的正式报告恰恰表明：大幅补偿通常有效，且大量“表面退化”病例仍在质心指标上改善。`Qraw` 很可能是与残差协同的中间表示，不宜按独立预测器惩罚。[R]

本计划提出 **SCQ-RF（Spatial Re-query Feedback）**：在保留原SCQ有效第一步的前提下，检验“修正后Q1重查询 Memory 邻域”能否相对于“继续使用Qraw旧邻域”的严格同容量对照，真正改善缺失骨块 E/J、覆盖和新发严重风险。[P]

**优先实验顺序是：F归因 → RF可行性 → RF-Static/RF-Requery结构对照 → 全量可靠性评价 → 多seed与独立确认。** 任何环节不通过都记录失败与停止原因，不自动调整权重、邻居数、loss、数据、排序或实验阈值。当前文件只定义可证伪的下一轮研究，不宣告任何SCQ-RF性能改善或临床有效性。

---

## 参考资料与核验说明

### A. 用户提供的研究报告（实验事实的唯一一手依据）

- **[R]** 《Cranial-BCSP-FullMamba：SCQ B／S阶段正式实验报告》v1，2026-11-14，15页，当前对话上传文件 `SCQ_BS_阶段正式实验报告_zh_v1.pdf`。本计划采用该报告实际冻结结果，不重算原始病例最近邻评分、不替换其中的源级指标口径。
- **[H]** 用户先前上传/提供的《Cranial-BCSP-FullMamba 本轮完整实验报告》2026-11-12、《Cranial-BCSP-Mamba P2 完整实验报告》2026-11-07及P1、P0与BCSP表示报告；仅用于说明既有负结果和冻结协议，不混合原始分值。

### B. 截至2026-11-14核验的公开论文与正式页面

1. Fu et al., *CompletionMamba: Taming State Space Model for Point Cloud Completion*, IEEE TIP, 2025. DOI: https://doi.org/10.1109/TIP.2025.3597041
2. Li, Yang, Fei, *3DMambaComplete: Exploring Structured State Space Model for Point Cloud Completion*, arXiv:2404.07106, 2024. https://arxiv.org/abs/2404.07106
3. Liang et al., *PointMamba: A Simple State Space Model for Point Cloud Analysis*, NeurIPS 2024. https://proceedings.neurips.cc/paper_files/paper/2024/hash/395371f778ebd4854b88521100af30ad-Abstract-Conference.html
4. Zhang et al., *Point Cloud Mamba: Point Cloud Learning via State Space Model*, AAAI 2025. https://doi.org/10.1609/aaai.v39i10.33098
5. Li et al., *DAPointMamba: Domain Adaptive Point Mamba for Point Cloud Completion*, AAAI 2026. https://doi.org/10.1609/aaai.v40i8.37596
6. Wu et al., *FusionMamba: Efficient 3D Point Cloud Completion via Spatially-Aware State Space Models and Multi-Scale Information Fusion*, Information Fusion 134:104378, 2026. https://doi.org/10.1016/j.inffus.2026.104378
7. Li et al., *BuildingComSSSM: Building Point Cloud Completion with Geometry-Aware Mambas*, IJAEOG 149:105269, 2026. https://doi.org/10.1016/j.jag.2026.105269
8. *CDRMamba: A Framework for Automated Craniomaxillofacial Defect Reconstruction Using Mamba-Based Modeling*, BSPC 103:107376, 2025. https://doi.org/10.1016/j.bspc.2024.107376
9. Kodym et al., *SkullBreak / SkullFix – Dataset for Automatic Cranial Implant Design...*, Data in Brief 35:106902, 2021. https://doi.org/10.1016/j.dib.2021.106902
10. Wodzinski et al., *Automatic Skull Reconstruction by Deep Learnable Symmetry Enforcement*, CMPB 263:108670, 2025. https://doi.org/10.1016/j.cmpb.2025.108670
11. Fishman et al., *Thickness and Design Features of Clinical Cranial Implants*, IJCARS 19:747–756, 2024. https://doi.org/10.1007/s11548-024-03068-4
12. Kwarciak & Wodzinski, *MedPCFM: Improving Medical Point Cloud Completion by Integrating Point Transformers and Flow Matching*, arXiv:2606.24433, 2026. https://arxiv.org/abs/2606.24433
13. Li et al., *Uncertainty Estimation and Probabilistic Skull Shape Reconstruction Using Bayesian Neural Networks*, Scientific Reports 16:16383, 2026. https://doi.org/10.1038/s41598-026-54679-7
14. Pathak et al., *Revisiting Point Cloud Completion: Are We Ready for the Real-World?*, ICCV 2025. https://doi.org/10.1109/ICCV51701.2025.02355
15. Bahri et al., *Spectral Informed Mamba for Robust Point Cloud Processing*, CVPR 2025. https://openaccess.thecvf.com/content/CVPR2025/html/Bahri_Spectral_Informed_Mamba_for_Robust_Point_Cloud_Processing_CVPR_2025_paper.html

**核验范围声明**：上述条目中，正式出版与研究目标主要根据期刊/会议开放页面、摘要及可用开放文本核验；没有逐一取得、精读用户全部所列论文的付费全文，也没有验证所有开源实现。具体技术差异/创新性结论必须在后续论文写作前进行全文与代码层面的近邻检索。任何公共论文的已有性能数字不得直接与当前SCQ的 `∂D→∂G`、来源划分和A1/A2评分混排排名。
