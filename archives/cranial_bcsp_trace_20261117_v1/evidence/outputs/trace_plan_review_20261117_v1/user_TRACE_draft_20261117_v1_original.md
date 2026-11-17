# Cranial-BCSP-FullMamba：BCSP-TRACE 正式实验计划书

> **中文名称**：探针—Memory空间证据追踪与锚点条件验证  
> **English**：BCSP-TRACE — **T**oken–probe **R**elations and **A**nchor **C**ondition **E**valuation  
> **文档性质**：科研预注册与可执行实验设计；**不是已实施实验报告，也不代表新模型已有效**。  
> **版本**：v1.0 / 2026-11-17；资料截止日：2026-11-17。  
> **当前决定**：封存 BCSP-SPCG 的 G2；**先做有限、可停止的 D0 机制诊断**。只有 D0 支持指定空间支撑假设且资产、计算图、资源均通过准入，才申请 D1/D2 正式训练。  
> **主任务**：SkullBreak BCSP Geo-V1，残缺实体骨组织完整边界 `∂D (8192)` → 缺失实体骨块完整边界 `∂G (8192)`，包含自由表面 E 与共享实体切除界面 J。**不是完整颅骨重建、仅外板面片补全、亦不是已认证的真实临床植入体设计。**

---

## 执行摘要（建议在实施前完整核对）

BCSP-SPCG 的 6 次从头训练、630 次 Native 预测、来源级 Bootstrap 与 5 例诊断已经完成。主要比较 G2（Sobol体积探针 + 局部8-Memory）相对 G1（相同头、全部256-Memory）的 E P95：**Fold C +1.5270 mm**、**Fold D +1.8720 mm**（候选−参考；正值为退化），D 折 95% 来源 Bootstrap 区间 **[+0.9379,+2.8983] mm**；G2 相对 G1 新增严重病例 **C 9、D 7**，分别挽回 **4、0**。Fold C 的 J Cover@2mm 虽提高 **7.0196 pp**，但没有在 D 折稳定复现，也未转化为完整骨块可靠性。G1 对 G0 也没有确立全面优势。因此**不能继续将固定 G2 当成有希望的优胜候选，更不能仅扫 k/探针数量或补一个残差头。**

该负结果没有辨明唯一根因：原 G2 同时改变了聚合基数（8 vs 256）、空间选择、平滑程度和梯度分布；Native 归档仅含 coarse/dense，没有实际 Memory/探针/邻居索引等机制数组。当前最具信息价值的问题是：**体积探针是否缺乏与 D 的有效几何支撑？如果有，此缺口与粗生成错位、漏覆盖是否存在可重复的关系？**

本计划提出分级检验：

1. **D0 / TRACE-Evidence（不训练）**：严格恢复已冻结 G1/G2 模型，在事先固定的开发病例上，用原输入与原权重进行有限 Native 只读重放；同时采集真实 `Memory(S,F,z)`、Sobol Probe、`KNN8`、输入描述子、Coarse 与 Dense。对证据进行几何支撑、Memory 使用、多样性和 Coarse 输出的成组分析；所有 GT 只参与离线诊断，绝不进入 Native 推理分支。
2. **D1 / TRACE-Anchor（条件式新结构）**：**仅在 D0 的预算门槛成立时**，将同一生成头中的 256 个体积 Sobol 探针替换为实际 Encoder Memory 的 256 个 D-only 空间坐标，邻域数量仍固定为8、相同 H 网络、相同损失、相同 Mamba Decoder；不叠加 SCQ/RF/DAC，也不使用 GT 或推理中的残颅/目标配准。
3. **D2 / 匹配训练（条件式）**：`G0-LQI / G2-Sobol-8 / G3-MemoryAnchor-8 × C/D` 六次 seed0 从头训练，核心比较 **G3−G2**，实用比较 **G3−G0**。要求同折初态/批次/设备配对，逐病例/来源评分、双向指标及新增严重风险；如 D0 不支持或任何准入失败，六次训练**不启动**。
4. **D3 / 扩展与确认（严格后置）**：只有研究候选在两折的主要 E/J、覆盖、CD、反向离群和新增严重方面均有可陈述的共同正向证据，再实施事先决定的额外训练种子与独立确认。已有 C/D 开发源被多轮使用，任何正向结果仍是**开发证据**，不能称盲测或临床验证。

**BCSP-TRACE 的创新位置目前是一个可证伪的研究问题，而不是论文级新颖性的预先宣称。** Memory 锚点、输入点位移、粗骨架与局部/全局条件在既有文献中均已有相关设计。只有完成严格对照、充分复现、医学任务适配与最近邻方法代码比较之后，才能讨论具体方法贡献。

---

## 1. 科学问题、事实与假设的层级

### 1.1 已冻结的经验事实（依据《BCSP-SPCG完整实验报告 v1》）

| 证据项 | G0 原 Coarse 头 | G1 Sobol+Global256 | G2 Sobol+Local8 | 可支持的结论 |
|---|---:|---:|---:|---|
| C E P95 (mm) | 8.8220 | 8.7319 | 10.2589 | G2 对 G1 的折内平均回退；区间跨0 |
| D E P95 (mm) | 5.8343 | 5.4049 | 7.2769 | G2 对 G1 的折内平均回退；来源区间全为不利方向 |
| C J P95 (mm) | 11.2788 | 11.5945 | 13.5252 | C G2 最差 |
| D J P95 (mm) | 7.8273 | 7.7237 | 9.9567 | D G2 最差 |
| C J Cover@2mm (%) | 44.46 | 39.85 | 46.87 | G2 局部覆盖高不代表完整几何好 |
| D J Cover@2mm (%) | 53.51 | 50.73 | 51.10 | 局部覆盖增益没有两折稳定复现 |
| C severe /105 | 10 | 6 | 11 | G2−G1：新增9、挽回4 |
| D severe /105 | 2 | 2 | 9 | G2−G1：新增7、挽回0 |

关键案例包括：`train__051__random_1`（G2 coarse/Dense质心约97.6/97.7 mm偏差，反向>20mm比例99.37%）、`train__072__random_1`（Coarse半径比约0.999而质心偏约89.8mm）、`train__008__random_2`（无远端>20mm点，但 E/J 漏覆盖且半径比约0.58）；`train__012__parietotemporal`和`train__046__parietotemporal`则有不同程度的改善，但后一例仍有较多多余几何。**这些只是冻结后的固定说明病例，不代表真实发生率。**

设备限制：C三臂及G0_D在原4090D，**G1_D/G2_D在另一4090D**，两张卡驱动同为570.190。本轮此前的 D 折 G1/G2 核心配对同设备；涉及 D 折 G0 的架构比较不是严格同设备对照。来源区间只量化固定训练模型对已开放来源的配对不确定性，**不覆盖训练seed方差、开发反复使用或临床泛化**。

### 1.2 竞争解释，均标记为“尚未证实”

- **H-A（空间支撑）**：体积 Sobol 探针多数位于实际骨组织 Memory 稀疏或不支持区域；少数真实 Memory 重复成为多探针的近邻，局部摘要缺乏特异性。
- **H-B（局部信息不足）**：即使探针距离 Memory 很近，局部8点平均仍无法表达未观测骨块的全局形状、双侧关系及整体空间方向。
- **H-C（条件利用失败）**：输入描述子具有空间差异，但全局 `z` 或共享头的权重主导输出，Query 槽位分散不足，`A/S/F` 的局部证据未被有效转化为正确 Coarse。
- **H-D（目标表达/不可观测性）**：仅凭 D 的若干局部邻居，缺失区域可能具有多种几何可能性；即使空间支撑改善，单次确定性256点生成也不一定能覆盖内外板和切壁。

以上四项可以并存。**不能从“Coarse已错”推导“探针是唯一原因”；不能从“改善质心”推导“形状修复”；不能把几何近邻距离直接转换成可信的失败概率。**

### 1.3 本轮正式研究问题

- **RQ-D0**：G2 的真实 Probe–Memory 支撑是否不足、是否具有跨折可解释的病例差异？该信息能否区分 H-A 与 H-B/H-C，而不仅仅复现已有 E P95 排名？
- **RQ-D1（仅条件式）**：若 H-A 有足够研究投资依据，固定相同 `k=8`、头部和训练合同，将体积探针换成**D-only Memory 空间锚点**，是否改善完整骨块 E/J、减少整块错位与漏覆盖？
- **RQ-D2**：新设计相对原 G0 的实用收益是否存在？是否因新增严重、接口近距离覆盖损失或远端离群而不适合晋级？

### 1.4 预先列出的反例和证伪结果

- 支撑距离确实变小，但粗生成依然整体错位：说明 H-A 不充分；不应继续按“更贴近D”扫描探针。
- 表面锚点主要来自残缺骨的已知区域，缺失骨块自由表面远离 D：G3 可能更加偏向输入骨表面，而不是缺失目标。
- 新模型更好地覆盖 J，却牺牲 E P95 或产生多余点：不能晋级。
- 半径从0.8提升到0.95，但出现80mm级骨块整体错位：不能晋级。
- Fold C 好、D 坏，或任一折出现大量新增严重：不能宣称稳定机制。
- D0 不能重现冻结的 G1/G2 Native 输出：停止；首先排查身份/输入/版本，不进行后续机制分析或新训练。

---

## 2. 与现有文献的关系：核验事实与原创性风险

**注意：以下“已核验”指本轮可以定位出版社/会议/预印本的标题、摘要或正文入口，不等于精读了用户82篇文献的全部原文和代码。用户以往整理的82篇按颅骨修复、Mamba/通用补全、2025–2026前沿和综述分组；未取得原文/实现的条目列入后续待核查清单。**

| 文献（截至2026-11-17可定位） | 已核验相关内容 | 对本实验的约束/启示 | 不能做的主张 |
|---|---|---|---|
| Li et al., **3DMambaComplete**, arXiv:2404.07106；2026 ACM TOMM版 | HyperPoint Generation 将输入降采样点与预测位移结合并展开细几何 | 输入相关的点/锚位生成已有先例；需对比对应公式和点位来源 | “首次从输入点生成coarse” |
| Fu et al., **CompletionMamba**, IEEE TIP 2025 | Mamba用于点云补全，强调局部几何和形状建模 | 局部信息不是天然新颖；要验证具体任务与可靠性 | “首次结合局部几何与Mamba” |
| Li et al., **DAPointMamba**, AAAI 2026 | Domain-adaptive PCC；分析序列化对局部拓扑的破坏，研究patch级几何关系 | 探针/Memory编号与空间对应需可追溯；任务与本项目不同 | 把其域适应结论当颅骨补全效果 |
| Wu et al., **FusionMamba**, Information Fusion 2026 | Spatially-aware SSM、local-global aggregation及几何补全 | H-B/H-C与现有融合工作重合风险高 | “首次空间感知局部全局融合” |
| Li et al., **Hyper-PCN**, CVPR 2026 | 超图高阶关系和结构协同 | 单点近邻不等于高阶结构；后续新颖性必须区分 | 仅添加anchor即可超越高阶方法 |
| **GDPNet**, 2026 | 通过 Keynodes Shift 等模块建立可靠coarse skeleton | 空间锚点/关键点变化已有相邻工作 | “首次从输入几何得到coarse骨架” |
| Kwarciak & Wodzinski, **MedPCFM**, arXiv 2026 | SkullFix/SkullBreak；PTv3确定性补全、扩散及Flow Matching比较 | 后续需有医学强基线与对齐任务语义；当前 BCSP ∂G 未必与其标签/协议相同 | 直接跨论文比较CD值 |
| Kwarciak & Wodzinski, **MedPCFM-TED**, MICCAI 2026 SASHIMI | 植入体点云的单步端点蒸馏与几何监督 | 生成路径的高效性和医学任务已有更新基线 | 把 workshop 模型误当本任务同协议排名 |
| Wodzinski et al., **Automatic Skull Reconstruction by Deep Learnable Symmetry Enforcement**, CMPB 2025 | 可学习对称性用于颅骨修复 | 对称性是另外的可能先验，当前不引入以免多因素 | 对称先验对双侧/额眶缺损必有效 |
| Kodym et al., **SkullBreak/SkullFix**, Data in Brief 2021 | 真实数据集背景与合成缺损来源 | 防止将公开合成来源冒充临床验证 | 把官方隐藏GT当已开放 |
| Fishman et al., **Thickness and design features...**, IJCARS 2024 | 临床植入体厚度、rim等设计特征 | ∂G 点云 E/J 与临床可制造implant必须区分 | J Cover@2mm = 临床合格 |

**用户文献库的其他相关标题线索**：PPC-MT、SymmCompletion、StruMamba3D、PPC-MT、Hyper-PCN、GenPC、RDS-Net、PCDreamer、Revisiting Point Cloud Completion Real-World 等；在未核验对应版本和全文/代码之前不对方法细节、原创性或数值作确定断言。文献审核顺序应先看与本方案最接近的“锚点/关键点定位、局部几何摘要、直接生成粗结构”，再比较训练/评价协议。

**明确的创新性边界**：即使 G3 获得收益，也首先只能说“在 BCSP 全Mamba、固定 k=8和特定数据协议下，D-only Encoder Memory 锚点比体积Sobol探针更有利于某些几何指标”。要作为论文创新，还需进一步解释与3DMambaComplete的HyperPoints/GDPNet的Keynodes Shift的实质区别，并提供跨seed与强基线证据。

---

## 3. 数据语义、划分和冻结评价对象

### 3.1 BCSP 任务合同

设完整骨组织实体 `C=D∪G`，体素前景中的残余骨 `D` 与移除骨块 `G` 不重叠。给定 `∂D` 的8192点输入，生成 `∂G` 的8192点完整边界。`∂D` 包括外侧/颅腔内侧/原有腔孔/人工切除暴露壁，`∂G=E∪J`，其中：

- `E`：G继承的原始骨组织自由边界，**不仅是颅骨外板**；
- `J`：与D共享的切除接触界面，仅用于既有BCSP任务语义；
- `D-only`：正向和所有预处理的空间条件只可从残缺输入D及其encoder输出获得，**不允许使用G或GT E/J mask、目标bbox、GT质心、临床标签、离线配准、人工病例失败标签。**

### 3.2 实验池及统计单位

- 已开放84来源×每来源5缺损=420病例，类型：`bilateral、frontoorbital、parietotemporal、random_1、random_2`。
- 同折：训练63来源315病例、开发21来源105病例；C/D开发来源互斥，但训练来源有42重叠并存在跨折角色交叉。
- 统一输入/输出8,192，Coarse 256，每中心FC生成32点；保持BCSP Geo-V1面积采样、原D-only归一化及真实world-mm逆变换。
- 骨块“患者”统计单位是**来源source**，不是五个缺损或每模型105个预测；全部评分先逐case，再同源5case等权，再21来源等权。不能将三模型630行当独立患者。
- C/D均曾多轮用于方法开发；**confirmation20仍封存**，未经完整方案冻结与新授权绝不访问；也不以SkullFix/MUG替代本轮确认。

### 3.3 已冻结评价器（不因新候选改变）

- `A1`：体素面积加权边界面中心，具有E/J区分；
- `A2`：每个A1面分四个子参考点，反向距离使用同一冻结参考；
- `Ref-B`：既定marching-cubes敏感度参考，不虚构其精确J身份；
- `E_P95`（主终点）：E面积加权参考→预测最近距离95分位（mm）；
- `J_P95`、`E/J Cover@0.5/1/2mm`、`CD-L1`（双向未平方距离均值半和）、`Pred→A2 P95`、`Pred→A2>20mm比例`；
- `severe_geometry := E_P95>20 mm OR J_Cover@2mm=0`、`placement_tail := dense centroid error>20mm`、`compact_distribution := radius_ratio<0.9`；均为**研究性标记而非临床标准**。

**数值复现硬合同**：加权P95的离散CDF定义为先按距离稳定排序、使用冻结FP64累积权重，并采用**排序累计权重末值×0.95**作为阈值，不替换为不同求和路径。SPCG历史审计曾因`weights.sum()`顺序造成约0.001014mm的J P95差异；不能用放宽容差掩盖定义不一致。完整统计另有具体实现SHA256，正式执行前从原证据核验，不根据本文直接改写实现。

---

## 4. D0：不训练的实际探针—Memory证据追踪

### 4.1 D0研究范围与预算上限

D0唯一目的是填补 SPCG 的 `NOT_COLLECTED` 空白并决定是否有充分依据投入 G3；**不是新增模型性能试验，不对已存在模型重新选择checkpoint，也不重新定义 E/J 评分。**

- 使用**原已冻结**的 G1/G2 C/D checkpoint 和同一开发case输入字节；只做 `eval/inference_mode`，FP32、TF32关闭、无BNCal/TTA/optimizer/backward。
- 抽取 **40 个已开放开发病例**，C、D各20；每折5类×每类4例。既有5个说明病例作为**已曝光压力案例**优先列入其真实fold与类型配额，其余按固定哈希补足。若配额冲突，预先记录固定优先级；不得查看新采集结果后补挑“好看”病例。
- 每fold优先不重复source_id（每fold有21个开发source、目标20例），source不重复条件与类型配额不冲突时保持；如发生冲突按预先固定哈希打破并在manifest披露。
- 仅G1/G2两臂，每案例各一次原生完整forward，总计 **80次full forward**；不做训练。仅在原同次forward调用中加观测hook，禁止修改用于模型的Tensor内容。为完整重放和定位，可在本机对采集张量离线计算派生统计，不追加训练。
- 所有五个历史压力案例的实际fold必须由冻结索引/manifest核验；**不得从`train__NNN`的名字推断fold**。
- 保存每模型真实权重身份、固定代码、input字节SHA、GPU/driver与每次forward计数，及采集前后模型状态和RNG见证值。修复因随机数状态/BN影响产生的输出差异之前，不得执行研究分析。

### 4.2 40例确定性抽样协议

候选池：冻结开发 C/D 所有case。规则：

1. 五个压力案例：`train__051__random_1`、`train__072__random_1`、`train__008__random_2`、`train__012__parietotemporal`、`train__046__parietotemporal`；精确来源/折以冻结报告的case索引为准。
2. 对每个fold×type桶，先放入属于该桶的固定压力案例；从未入选的同桶样本中，按 `SHA256("BCSP_TRACE_D0_v1|"+fold+"|"+canonical_case_id)` 字典序升序补到4例。优先选择新source，若来源重复不可避免，使用固定哈希次序继续补足，不回填别的类型。
3. 输出一个完整 `selected40_v1.json`，包含fold/source/type/case_id/来源证据/压力或哈希入选理由/实际输入路径哈希。**名单在第一次采集forward前冻结**。
4. 40例不是新盲测：5例有意困难，剩余为确定性开发样本，因此不得把40例占比当成总体严重失败率。若后续关联分析按类别汇总，必须同时给出压力与非压力分层。

### 4.3 必须采集的原始Tensor及派生证据

| 字段 | 形状/精度（省略batch=1） | 来源 | 必须检查 |
|---|---|---|---|
| `input_D_norm` | 8192×3 FP32 | 正式同次D输入 | 仅D-only; SHA对应原输入 |
| `memory_S` | 256×3 FP32 | 真正进入head的encoder Memory坐标 | 与F编号严格对齐 |
| `memory_F` | 256×384 FP32 | 实际Memory特征 | 不能替换为对GT重采样的tokens |
| `global_z` | 1024 FP32 | 全局特征 | 不用GT定义它 |
| `probe_U` | 256×3 FP32 | 固定Sobol字节 | 与原SPCG冻结文件SHA匹配 |
| `probe_A` | 256×3 FP32 | bbox(D)映射 | 精确复核公式，非GT位置 |
| `neighbor_idx` | 256×8 INT64（G2） | 实际KNN选择 | 与独立距离重算完全一致；ties按原规则 |
| `neighbor_distance` | 256×8 FP32/FP64 | 由S/A离线重算 | 单位为D-only normalized，不冒充mm |
| `f_i,mu_i,rho_i,tau_i` | 256×(384,3,1,1) | 真实head描述子 | 确认原head实际消费 |
| `head_input_x` | 256×1416 FP32 | 生成头输入 | 验证拼接与数值有限 |
| `coarse_Q` | 256×3 FP32 | 同次生成头输出 | 与历史Native coarse复演吻合 |
| `dense_P` | 8192×3 FP32 | 原LQI/FC输出 | 与历史Native prediction复演吻合 |
| `model/checkpoint/input_fingerprint` | 文本/哈希 | 审计 | 复现时不依赖文件basename |

G1的`neighbor_idx`应使用**全部256 Memory**，不伪装成8近邻；其f/μ/ρ/τ按原G1定义记录。统一保存数据版本、dtype、数组endianness、shape、单位/归一化，以及模型本次真实输入，不要只写一个字段名而缺少真实字节。

**最低成功条件**：同一模型的`Q/P`与历史冻结预测通过原数值合同校验（优先逐字节/逐元素；如CUDA执行存在可接受的微小差异，须预先采用训练项目已验证的`atol/rtol`，并证明 E/J风险标签、源级聚合未改变）。若不能复现，则**D0停止**，把问题列为恢复失败而不是医学机制负面结果。

### 4.4 只由 D/S/A 计算的空间支撑诊断量

定义Memory自身的典型间隔：

\[
\ell_S=\operatorname{median}_{j}\min_{k\ne j}\|S_j-S_k\|_2+10^{-8},\qquad d_{ik}=\|A_i-S_{N_{ik}}\|_2.
\]

为避免D-only归一化尺度随病例变化导致误读，主要支撑量采用内部无量纲比值：

\[
r_i=\frac{d_{i1}}{\ell_S},\quad t_i=\frac{d_{i8}}{\ell_S},\quad
u_{case}=\frac1{256}\sum_{i=1}^{256}\mathbf 1[r_i>2].
\]

**定义不是阈值临床意义**：`r_i>2`仅是预先固定的**研究型低支撑标记**，并非“点无解剖依据”的充分条件，不据它在 Native 中做推理拒绝。还应记录：

- `d_D(A_i)=min_{x∈D}||A_i-x||`，与`d_{i1}`分开；D原始8192与实际Memory S不是同一离散尺度；
- 邻域利用率 `U=|∪_{i}N_i|/256`、各Memory Token被命中次数分布、归一化 Shannon Entropy（`p_j`按所有2048次命中归一化）；
- 有效邻域的离散程度 `σ_S(i)`、邻居坐标协方差谱/条件数（退化附近需稳定eps），避免无依据把谱分裂叫“内外板识别”；
- 探针位于D-only bbox内的相对位置、表面附近/内部距离分布；对比实际S锚点的D-only支撑性质；
- 256个 head 输入描述子的有效差异、槽位输出Q最小间距、分布半径、协方差谱、pairwise距离的分位数；
- 原 `Q` 是否主要由相同或极近的探针局部条件生成；如使用Spearman关联，按case及fold分别报告，不把256个query当独立患者。

**重要对照**：G1全局256的每探针`f_i`与`tau_i`在原定义下可能相同，G2则不同；应实测此事实而非把不同的方差宣称为更正确的几何信息。

### 4.5 引入 GT 的离线关系分析（仅诊断，不进入forward）

完整G、A1(E/J)、A2只允许进入**离线分析与冻结评分读取**，不得改变上一步任何生成条件。以下比较均是描述性而非因果：

1. 将相同case的G2−G1历史E P95、J P95、J Cover、CD、远端离群及严重转移与`ν_case、U、熵、r_i/t_i分位数、Q多样性`关联；**先按fold与压力/哈希组分别呈现，再合并仅做描述**。
2. 对G2失败三例及两个改善对照，展示`D/S/A/Q/P/GT`同一物理坐标系的全局正交投影；GT只用于着色与评分，不能用来选择/移动探针。
3. 以预测Q到GT G8192的最近距离/Coarse E/J P95作为**关联解释量**，明确它不提供跨Query解剖点对应。Coarse256与Dense8192不可直接把P95变化归为模块因果，因为点数不同。
4. 对每个来源最多按实际选到的病例聚合一次；若不同类型取自同一source，不把它们当独立来源。置信区间只在有足够独立来源和预先规定分层的情况下探索性报告；**不追加假装正式统计显著性**。

### 4.6 D0输出材料与停止准则

必须交付：`selected40_v1.json`、`model_input_identity_v1.json`、`replay_match_v1.json`、`spatial_support_metrics_v1.csv`、`case_level_association_v1.csv`、`fixed40_mechanism_review_v1.md`、`manifest.sha256`及一个明确的`D0_GO_NO_GO.json`。指标统计文件需包含分母、折、来源、type、压力选择标记、单位和生成源码哈希。

**D0不满足以下任一条件即NO-GO**：

- 不能恢复完整 checkpoint + factory + 数据同字节身份；
- 任一预定采集字段实际缺失、shape不符或S/F编号不一致；
- 80次上限内无法使原Q/P复现原Native数值合同；
- 真实Memory上存在无法解释的严重重复/索引错误，使G3的256独立锚点无法构造；
- 支撑分析不足以提供与“局部8丢失全局信息/共享头条件利用失败”相区分的证据，或仅凭五个有意选择的历史失败例才显示关系。

**研究投资用（非统计/临床）预登记门槛**：固定`r_i>2`定义后，要求两折各至少一半预选case出现`ν_case≥0.50`，并且在各折的非压力来源里，`ν_case`与G2−G1 E P95差值的Spearman相关方向**均不为负**；实际效应大小、source分母与不确定性必须同表披露。该门槛意在避免仅因“体积探针离表面远”这一几何显然事实就追加六run，**不是模型性能的证明，也不是可信推理风险判据**。若不满足则本方案只提交负面/不确定诊断并停止，不事后改阈值或扩容病例。

该门槛有一定保守性且样本小；它只是是否值得投入**下一轮条件训练**的预算规则，不能由其正负推断普遍的医学因果事实。尤其在D-only输入是薄壳几何时，Sobol点离壳远很常见，这本身不能证明其会导致生成失败。

---

## 5. D1：仅在D0 GO后冻结的最小结构候选 TRACE-Anchor

### 5.1 选择单一自由度，不继续迭代残差

**G3-MemoryAnchor-8**：使用原 Encoder 实际 Memory 的256个D-only坐标作为第一阶段直接Coarse生成的256个空间锚点；保持 G2 原局部8-Memory邻域选择、描述子结构与共享MLP，直接输出Q。主要改变是**空间探针的来源**，不是新增注意力、SCQ/RF/DAC、第三头或loss。

与G2的关键差异：

| 属性 | G2-Sobol-8（条件式匹配重训） | G3-MemoryAnchor-8 | 因果解释范围 |
|---|---|---|---|
| 锚点 `A_i` | D-only bbox上的固定Sobol三维探针 | `A_i=S_i`实际Memory坐标 | 探针来源/空间支持的**组合效应** |
| 局部聚合数量 | KNN8 | KNN8 | **k不变** |
| 总Memory数量 | 256 | 256 | 相同Encoder，均可从S/F查询 |
| Head输入 | `[z,f_i,A_i,μ_i,ρ_i,τ_i]` | 同1416维描述 | 相同通道/数学定义 |
| Head网络 | 1416→1024→384→3 | 完全相同 | 完全同容量同初态 |
| 输出 | 直接Q256→原LQI/FC | 同 | 无新反馈/参数惩罚 |
| 真值信息 | 仅loss训练，推理不见GT | 同 | 不得使用GT bbox/接口mask |

`A_i=S_i`会使该锚点自身成为KNN的一个零距离邻居，并将FPS/Memory坐标序的空间分布带入生成。这些是更改锚点来源的**已知后果**，因此即使G3获益，也不能把效果完全等同于“最近距离缩短”这一单一因素的纯因果贡献。**本轮估计的是“Memory表面锚点替代体积探针”的完整训练配置效应。**

### 5.2 形式化定义

输入D经过原无attention FullMamba Encoder，获得实际 `S∈R^{B×256×3}`、`F∈R^{B×256×384}`、`z∈R^{B×1024}`。令

\[
A_i^{(G2)}=\ell(D)+[h(D)-\ell(D)]\odot U_i,\qquad
A_i^{(G3)}=S_i.
\]

对于`m∈{G2,G3}`：

\[
N_i^{m}=\operatorname{KNN}_8(S,A_i^{m}),\quad
\widehat F_j=\operatorname{LN}_{\mathrm{no\ affine}}(F_j),
\]
\[
f_i=\frac18\sum_{j\in N_i^m}\widehat F_j,\qquad
\mu_i=\frac18\sum_{j\in N_i^m}(S_j-A_i^m),
\]
\[
\rho_i=\frac18\sum_{j\in N_i^m}\|S_j-A_i^m\|_2,\quad
\tau_i=\sqrt{\frac18\sum_{j\in N_i^m}\|(S_j-A_i^m)-\mu_i\|_2^2+10^{-6}},
\]
\[
x_i=[z,f_i,A_i^m,\mu_i,\rho_i,\tau_i]\in\mathbb R^{1416},\quad
Q_i=H(x_i),\qquad H:1416\to1024\to384\to3.
\]

两隐藏层为GELU、末层线性含bias；`LN`每Memory Token无仿射、eps=1e−5。无`Q=A+Δ`，无clip/tanh、无投影到D表面、无GT输入。**G3虽然锚点在D上，预测Q不受D表面/包围盒限制**；缺失骨块远离已见骨表面也必须有生成自由度。

### 5.3 计算图接口和排序一致性

- 只替换 `PCTransformer.forward` 中首次 `learned_coarse` 赋值；所有后续 `mlp_query`、Query位置编码、已有LQI Mamba decoder、Query排序/逆序、FC点生成、输出coarse与原训练loss不变。
- 仍使用已有6层Encoder与8层LQI Decoder；不新增Transformer self/cross-attention分支。Mamba之外的FPS/KNN/MLP/归一化允许存在，不声称全网络严格线性。
- G2保持固定U序；G3的`A_i=S_i`与真实S/F索引对齐。训练前进行**固定权重、同样输入的探针置换检查**：只对作为集合输入的锚点做一致置换，输出经相同置换逆变换后应符合共享H及后续排序合同；若实际Decoder显著依赖外部探针编号且不具置换一致性，不得把G3−G2归因为纯空间支撑，应修订为“锚点来源+序列位置的联合效应”并重新冻结实验合同，**不能静默重排旧代码。**
- S/F若来自FPS，S坐标本身可能无梯度，这属于输入D-only几何；所有有梯度的F、z、H、后续网络仍要通过原loss获得有限梯度。不为了“可微锚点”新增未注册的坐标回归路径。

### 5.4 严格容量与初始化

- G2/G3两个直接生成头与原SPCG报告相同结构；目标原生模型参数量各为**39,912,132**（仅在factory/源码身份未变时成立，实施时重新实测确认）。
- G0原LQI头为**39,903,169**参数，与G2/G3不同；G0是实用基线，不是精确等容量对照。
- 以冻结head初始化字节或同一个预生成初始化包为权威；同折G2/G3的所有可训练参数、持久buffer须逐名/shape/dtype/内容哈希配对。G0共享Encoder/LQI/FC初态，原head保留其旧规则。
- 禁止为了“更好收敛”对G3额外使用零初始化、warmstart G2、train-only重投影、辅助GT约束或不同BN/调度。

### 5.5 无GT准入的失败测试

- 仅在输入D上计算真实Memory并构造 A，绝不访问目标G/BBox/切壁标签；
- 若Memory坐标重复（数值容差另在实现时冻结）导致有效锚点显著少于256，应停止并披露，不能临时替换成FPS新数据或Hungarian assignment；
- G3的`KNN8`包含自身零距离是已定义行为，不能在训练中根据开发结果决定是否排除self；
- 必须核验每个生成Q均由该head真正消费到LQI/FC和coarse loss，不是只替换导出的坐标；
- 如果G3的初始 Q 坍缩或梯度非有限，先定位实现/数值合同，不将其描述为正式科研负结果，也不加临时正则补救。

---

## 6. D1数学/CPU/真实CUDA准入（零优化更新）

**顺序**：纸面公式/参数量复核 → 纯CPU最小人工合同 → 真实母版CPU可覆盖接口检查 → Native CUDA零更新前向和完整loss/backward → 只读冻结准入。

### 6.1 最小人工CPU合同

至少涵盖：

1. D-only probe、S/F索引、KNN8 tie、全零/近零跨度、非有限输入、固定U字节；
2. `x=[z,f,A,μ,ρ,τ]`正确1416维，μ/ρ/τ独立NumPy/float64重算；
3. k=8，256 token，不读GT、无外部mask/Oracle、没有临时GT相关路由；
4. G2/G3所有参数及持久buffer同初态；模型参数量、optimizer分组及no-decay按原合同；
5. F/z/H以及后续query MLP/Decoder/FC对原loss的有限有效梯度；
6. 同一输入的重放一致性、模式/RNG/BN恢复；
7. Query重排/置换检查、重复Memory坐标、防止输出顺序/点数混乱；
8. 关闭SCQ/RF/DAC、额外rim/位置/尺度loss、BNCal/TTA/自动resume等历史路径。

### 6.2 真实CUDA合同

建议最小固定准入序列：`G0_eval1、G2_eval1、G3_eval1、G2_train8、G3_train8`；共**5次forward、2次完整loss/backward、0次optimizer.step**（若实现/原生provider有明确额外必要，须先改协议版本并标记原因）。训练模式必须同时验证BN和原生Mamba梯度；不使用人工CPU结果替代CUDA。

验收包括真实22个SSM mixer路径及预期调用次数、dtype、有限数值、coarse/dense shape、所有输出坐标消费者、Gradient norm、weight decay、状态/RNG恢复、显存资源；**准入通过不意味着医学效果有效**。

### 6.3 不可接受的准入偏差

- 训练新候选前更换数据、点数、真实Memory来源、Mamba kernel或loss实现而不记录；
- CUDA出错后未经原因定位静默自动重试并覆盖旧记录；
- 只检测loss减小便认定G3胜出；
- 因G3失败而在相同候选名下改k/epsilon/Sobol排列/锚点排布。

---

## 7. D2条件式训练矩阵与对照层级

### 7.1 第一批六run（仅D0 GO且D1准入通过后）

| 训练ID | Fold | 模型 | 头部/探针 | 目的 |
|---|---|---|---|---|
| `TRACE_G0_C_s0` | C | G0-LQI | 原1024→1024→768 | 当轮实用主基线 |
| `TRACE_G2_C_s0` | C | G2-Sobol8 | 既有局部8 + 固定bbox Sobol | 与G3精确同容量 |
| `TRACE_G3_C_s0` | C | G3-MemoryAnchor8 | 同样局部8 + 实际S坐标 | 主要研究候选 |
| `TRACE_G0_D_s0` | D | G0-LQI | 原头 | D折当轮实用主基线 |
| `TRACE_G2_D_s0` | D | G2-Sobol8 | 同C | 与G3精确同容量 |
| `TRACE_G3_D_s0` | D | G3-MemoryAnchor8 | 同C | D折复核 |

**为何不直接复用SPCG旧G2分数？** 当前实验需要G2/G3在同一配对合同和设备内训练。旧G2的C/D设备与旧G0不完全一致，且当前将增加机制采集/置换准入；即使模型名字一致也不能把跨轮历史值替代正式匹配对照。G1旧模型只作为辅助背景和D0诊断对象，**不自动增加第7/第8次训练**。

### 7.2 预算、模型选择与实现边界

- 每run：batch8，63来源315病例，100次遍历×39批=**3900次optimizer更新**、每run31200曝光与300drop；六run合计23400更新、187200曝光与1800drop。
- 原AdamW：lr=1e−4，betas(0.9,0.999)，eps=1e−8，实际参数组weight decay仅0/5e−4；原梯度clip10，FP32、TF32=false；继承历史LR/BN动量调度的**源码与逐step轨迹**。
- 只保留最终epoch99/step3900为主比较；不按开发集挑epoch、调warmup、保存所谓最优模型、自动resume或改变drop_last。
- 损失完全沿用原 `coarse Chamfer + dense Chamfer` 与PyTorch `cdist`及归约；不加入位置、法向、尺度、对称性、J、厚度、置信度、delta损失。
- 所有G2/G3同折初态及实际batch顺序必须匹配，G0共享母版初态；将训练中的数据哈希、实际order与LR/BN轨迹冻结，不把seed整数名字当成配对证明。
- 最理想六run全在**同一张GPU、相同驱动/容器**完成；若设备中断，只允许在单个fold内始终保持两臂G2/G3同一物理设备。无法保持时报告该折机制比较为混杂/未裁决，**不得用另一设备历史分数填补**。
- 原先4090D训练典型torch peak allocated约12.93–12.97GiB，资源只供估算：预先设实际Torch峰值≤20GiB、SMI≤22528MiB、RSS≤8GiB、每run墙钟≤3600s；输出与checkpoint盘需实际检查，建议自由盘预留≥12GiB，不将采样资源监控当专属硬隔离。

### 7.3 第二训练种子安排（明确条件式，不冒充完整验证）

前六run是**seed0开发性筛查**，后续是否启动另一独立初始化seed必须在任何D2评分前形成书面协议。建议默认**只有两折、E/J、风险均达到第9章事先定义的晋级条件，才启动完整 `G0/G2/G3×C/D` 六run seed1**；一旦启动，不因seed1中途出现不利结果选择性停止某一臂或删除结果。

这属于资源保守的两阶段设计：通过筛查的候选得到更多开发证据，但**不是无选择偏差的确认性试验**。若论文核心结论需要统计训练方差，应在另一个完整确认协议中预留至少两个或更多固定种子，不能仅因首个seed好看就选择性追加并宣称独立验证。额外seed的配对实际batch顺序与初始化规则必须独立冻结。

---

## 8. Native预测、评分与数据产物合同

### 8.1 正式预测

六个训练模型各预测其开发105例，合计**630个Native model forward**。所有模型batch1、原eval模式、不warmup、BNCal、TTA、GT配准、ICP、中心迁移、后处理、删离群或根据E/J结果拒绝病例。

在同一次真实forward中必存：`prediction[8192,3]`、`coarse[256,3]`、`input_D_norm`、`probe_A`（G0可标记N/A，非伪造探针）、`memory_S`、`memory_F`、`global_z`、`neighbor_idx`、`f_i/μ_i/ρ_i/τ_i`、`head_input_x`及身份元数据。若完整保存每例Memory导致资源超限，**在训练前而不是预测后**冻结“全部case存P/Q，固定来源分层case存内部机制张量”的明确两级采集合同；不得把省略后的产物声称为全量机制证据。

建议**优先全量P/Q与轻量支撑摘要，完整内部张量至少用于与D0相同的固定40个病例**。如果打算全量存储，应提前核对bytes预算并在训练前写进request，不自动改变归档大小上限。所有模型同fold使用相同选样。

### 8.2 统一评分

- 模型行：6×105=**630**；共享控制`Nop_D`与`GT8192`各开发case一条，合计210×2=**420**；正式评分总**1050病例行**，共享控制不能当作额外训练模型。
- 先病例后来源等权，不使用对所有点拼接计算的“总体P95”；引用既有A1/A2/Ref-B，不更改面积权重或J定义。
- 预定比较顺序：**主因果范围 G3−G2**（同参数、k=8、不同探针来源）；**实用 G3−G0**（容量不完全相等）、**辅助 G2−G0**（同轮重训背景）。三个比较两折全部报告。
- 绝对表与配对表需同时含`E_P95、J_P95、E/J Cover@0.5/1/2mm、CD-L1、Reverse A2 P95、A2>20mm比例、质心偏差、回转半径比`。
- 依照固定 `severe` 定义分别统计`原严重→非严重、原非严重→严重、共同严重`，并报告完整病例id及对应来源，不只写严重数净变化。
- 五种缺损类型每折均21病例，按fold×type完整列出差异；**不能根据分类型正负结果事后排除难例、挑最好的缺损类型作为“正式任务”**。

### 8.3 来源级统计方案

沿用前期已审核的**每折21来源 paired bootstrap 2000次**，来源顺序按canonical_source_id字典序，使用`Generator(PCG64)`与预先独立冻结的固定种子，例如C=2026111701、D=2026111702；对同一折全部比较与指标使用完全相同的2000×21抽样索引矩阵并保存NPY+SHA。

估计量为来源均值差；95% percentile interval = `quantile([0.025,0.975], method='linear')`。不补做p值/多重比较/BCa后假装预设；区间反映固定训练模型在这批**已曝光来源**的变化，不涵盖训练seed方差或跨折训练角色重叠。严禁将210个病例视为独立来源得到过窄区间。

---

## 9. 主要终点与预先冻结的GO/NO-GO规则

### 9.1 判据层级

- **首要**：G3−G2在**C与D两折 E_P95 均为负**；来源胜负、中位数和区间不得与均值所指方向形成明显矛盾。
- **必要一致性**：两折J_P95不出现明显相反的系统性恶化；J Cover@2mm不得通过显著损失近距离接口支持换取E小幅下降；CD-L1、E Cover及反向离群至少不呈普遍不利方向。
- **硬风险目标**：两折 `G3−G2 new_severe=0` 为本阶段保守晋级必要条件（不是临床标准）；同时完整报告挽回、共同严重和`placement_tail/compact_distribution`转移。
- **实用性**：G3相对当轮G0的E/J、CD、覆盖与风险应形成可辩护的联合收益；只比旧已淘汰G2好、却明显落后G0，不支持论文主候选。
- **复现**：任何单fold的均值优势都不得写成跨折稳定；bootstrap区间跨零时应表述为证据不充分，**不能写成等效**。没有多seed不能声称稳定训练或临床可用。

### 9.2 明确的NO-GO情况

1. D0不支持“体积探针空间支撑不足”的机制投资假设，或无法复演原Native；
2. 任何训练/评分前置合同失败且无法在预注册版本内恢复；
3. 一折 E P95 改善、另一折反向退化，即使两折平均下降；
4. 新增严重病例（按既有阈值），尤其整块错位/零J接触；
5. 仅Coarse质心/半径或局部J Cover改善，最终E/J尾部、CD或反向离群退化；
6. 仅选择一个source/缺损类型或一次seed的结果才看见优势；
7. D1为了改善当前开发集结果临时更改锚点、k、隐藏层、排序、初始化、loss或病例清单。

### 9.3 预先规定的结果解释

| 结果模式 | 正确解读 | 决策 |
|---|---|---|
| D0不显示有辨识度的支撑不足 | 不支持H-A优先地位；H-B/H-C尚待独立研究 | **停止 G3**，只交付诊断报告 |
| G3在两折均改善 E/J、风险可接受且优于G0 | Memory锚点配置有开发性正向证据 | 进入独立seed/方法对比，不宣称首创 |
| G3优于G2但不如G0 | 减少某种旧探针问题，仍不足以成为实用方法 | 不晋级；存档负面/混合证据 |
| G3改善位置/半径，却损害 E/J或新增严重 | 低阶矩与完整骨块脱钩 | 停止，不叠加补救头 |
| G3某折改善另一折失败 | 折/来源异质性仍显著 | 停止，不改折或筛例 |
| G3对G2差异小、无法区分 | 该锚点替换未提供可辩护额外价值 | 停止；若需效应界需另立协议 |

**研究型硬门的使用边界**：零新增是保守预算决策，而不是“新方法必须在任何现实病例零失误”的临床承诺；统计结果无论正负都要保留。如果未来采用更宽容的风险接受范围，必须在下一**独立**实验开始前重新预注册，不可在看到本轮分数后修改本轮门槛。

---

## 10. 机制解释深化：为什么必须同时保留全局与局部证据

- SPCG的G1/G2差异同时涉及`k=256→k=8`，因而此前“空间局部性导致退化”尚无纯净证明。TRACE-G2/G3虽然均使用k=8，仍改变了锚点采样来源、零距离自身邻域、token空间分布等；它检验的是**锚点来源组合效应**，不把它写成“空间支撑距离的独立因果效应”。
- G3 Memory锚点贴近D，只证明对**已观察输入表面**具有局部支持，**不会自动说明该锚点对应未观察的G骨块位置**。真正的完整形状、E/J分区和空间外推必须由全局z及共享生成头学习，不存在基于GT的条件捷径。
- 对Coarse使用256点、Dense使用8192点的有向NN差异，既含分布/形状差异又含点数预算差异；要定位阶段，不应直接以Dense P95更低宣称LQI修正了所有Coarse错误。
- 如果旧Memory本身覆盖不足（例如大缺损另一侧缺失），直接以其S作探针可能加重错位。故仅在D0具备正向机制动机后训练，且保持G0作为可用参照。
- 如果真实诊断更支持H-B（全局信息不足），再设计**相同k的非局部/局部融合**对照；如果更支持H-C（head未利用条件），需要另外定义槽位/条件敏感性实验。**两者不属于本TRACE的条件式G3，不自动追加训练。**

---

## 11. 公平性、资源、复现和风险管理

### 11.1 设备与可恢复资产

原SPCG有6个最终checkpoint身份哈希，但报告明确没有重新验证全部本机长期备份。正式D0需要G1/G2 C/D原权重、原factory、Sobol probe原字节、原输入/评分器/预测档；任何缺失应在资产台账标记为`MISSING`，不能凭文件名构造恢复路径。

关键已知身份参考（实施前仍须从冻结事实文件独立复核）：

| 旧SPCG资产 | SHA256 |
|---|---|
| G1_C | `dd5ad567eadc66ef1b47d708128f48aa2221ee1df6bbd954b830cc59a11835ce` |
| G2_C | `7b0ee55071b8a4d3d916e9324fd306c5edcdea4079f3c30851591f99651376d8` |
| G1_D | `beac40e64a15eba8be8c6c583eca1d2171ccf293d96ba1dbc9dd51c9811dd275` |
| G2_D | `61aec7309b20a67bb0db74dcec7a78d3148265e80fd04fff6699ca0d459ededb` |
| 原Sobol U字节 | `ba87509aedc575f9b2db006025417261f8d478461e79518c4e8c0d83c6efcbbf` |
| 原H初始化字节 | `e0177f8ae5d1da31c4eb2f0bfd2d0ec8844255b00dcf31307fbbd33f43346b39` |

源报告路径使用历史Windows `E:/...` 和 Linux 训练容器，二者**不是共享文件系统**；本文不会假定这些路径在新服务器可直接访问或已获操作授权。项目资产归档必须以真实sha/bytes和恢复测试为准，不是仅有哈希列表。

### 11.2 数据与方法版本治理

- 一次训练只能对应一个不可变`run_id`、fold、seed、模型arm、训练平台、输入列表与code hash；失败的执行记录保留，不覆盖旧run身份。
- 训练前同时冻结：D0名单、D1数学公式、代码、checkpoint初态、完整batch序、原评分器、统计脚本、运行资源限额、预期输出字段。
- 所有产物通过完成码、hash、count、有限值、shape和来源身份复核；正式的审计是“可追溯与内部一致性”，并不等于另外一个独立数学实现已重新证明全部NN距离正确。
- 资源日志采样可能漏掉瞬时峰值，报告Torch peak与SMI采样的不同口径，不用单次训练耗时宣称Mamba算法优于Transformer。
- 不因负结果扩大到同一开发集的新病例/新的loss/新的探针；如真的需要新实验，必须重新立项并声明旧开发已曝光。

### 11.3 工程故障与科研负面的区分

预测路径错误、checkpoint恢复失败、KNN索引与S/F不一致、FP32/CD后端变化、启动设备标识不匹配属于**执行中断**，不能记为模型科研负分。只有符合固定合同的成功训练与原生评分才能进入负面/正面科研比较。

### 11.4 风险台账

| 风险 | 触发场景 | 预防措施 | 发生后决策 |
|---|---|---|---|
| D0采集缺失 | 内部Tensor未被保存或head输入与Q/P不一致 | 原生hook与完成manifest逐字段校验 | 停止后续训练 |
| Probe表面偏置 | G3锚点均贴D，未见G远离D | 保持全局z、允许Q离开D、联合E/J评价 | 正式记录，无后验投影 |
| Memory坐标重复/退化 | 有效唯一锚点不足 | 先做S唯一性和距离测试 | 停止，不临时加FPS/assignment |
| Mamba数值漂移 | 相同seed不同训练轨迹 | 真实权重/顺序/设备配对，披露有限确定性 | 不归咎于浮点微差而无证据 |
| Fold差异 | C/D方向不同 | 预先固定两折均需正向主结果 | NO-GO |
| 风险转移 | 新增severe | 逐case新增/挽回和反向离群全报 | NO-GO |
| 源级相关/开发反复使用 | 重复样本当独立患者 | 来源级均值/Bootstrap，保留曝光属性 | 不称确认性结论 |
| 临床外推 | E/J指标被写成植入安全 | 另需厚度、接触/水密/可制造与临床数据 | 不进行临床主张 |

---

## 12. 时间与最小预算安排（不承诺异步交付）

| 阶段 | 内容 | 上限/资源 | 交付物 | GO/NO-GO |
|---|---|---|---|---|
| TRACE-P0 | 资产清单、40例名单、模型身份恢复 | 0训练、0预测 | `asset_manifest`,`selected40` | 欠缺必须资产则停 |
| TRACE-D0 | 真实G1/G2×40例采集及关系分析 | 最多80次full forward，0更新 | 真实Memory/Probe/索引与D0报告 | 依据第4.6节决策 |
| TRACE-C0 | G3最小实现及CPU/CUDA合同 | 5次原生CUDA forward、2backward、0step | 数学/梯度/性能准入报告 | 不通过则停 |
| TRACE-T0 | G0/G2/G3×C/D seed0 | **条件式6×3900=23400更新** | 6ckpt、参数/顺序审计 | 训练合同失败则停 |
| TRACE-E0 | 630 Native + 420控制行评分 | 630 Native、1050评分 | 来源级E/J/CD/风险表、bootstrap | 第9章联合判据 |
| TRACE-T1 | 第二独立seed成组复验 | 最多条件式额外6run | seed层级稳定性 | 不对阳性择优 |
| 后续独立确认 | 未曝光来源/SkullFix/强基线 | 另行严格协议 | 可发表的独立证据 | 不自动启动 |

实际墙钟取决于模型和环境，旧SPCG单run约25分钟只是历史资源记录，**不作为对新设备、自动运行或将来交付时间的保证**。TRACE-D0是最小应优先执行的阶段；任何新训练都要按权限和预算单独实施，不应把计划文件理解为服务器操作授权。

---

## 13. 预期论文结果表达与最低证据层级

### 13.1 合法结果表达模板

- **D0支持空间支撑缺口但G3退化**：“观察到体积探针对实际Memory的若干低支撑特征；以Memory空间锚点替换体积探针未改善固定BCSP协议的完整骨块质量，提示仅改善输入锚点支撑仍不足以保证未观测形状恢复。”
- **D0支持且G3跨折开发收益**：“在固定Mamba生成路径与k=8下，输入Memory锚点相对Sobol探针具有开发集几何收益；其新颖性、跨seed稳定性与医学适用性仍需验证。”
- **D0不支持，因而无G3训练**：“已完成机制追踪，未取得足以将探针支撑优先确定为下一预算投入方向的证据，故依据预注册决定不训练候选。”
- **G3仅优于G2未优于G0**：“表面锚点能缓解旧探针候选某些失败，但未形成相对原LQI实用基线的综合性能优势，不晋级。”

### 13.2 论文级证据仍缺什么

1. 相对于原LQI及AdaPoinTr-Implant等**同完整骨块任务口径**强基线的可比实验；已在外部论文发布的指标必须重新核对任务、采样、点数和world-mm定义后才比较。
2. 与3DMambaComplete、FusionMamba、GDPNet、Hyper-PCN等最近邻工作在结构与消融上的明确区别；不能仅替换名词。
3. 至少额外预登记训练种子及模型容量、显存、原生推理时延的可复现实测；不能从参数量相近推断效率或统计稳定性。
4. 未参与调参/设门的独立来源；不同折训练重叠不能冒充独立训练复制。
5. SkullFix迁移及必要的医学边界、厚度、临床植入体与仿真完整骨块区分。MUG不能无证据标记为高精度真实GT。

---

## 14. 可供执行的伪代码与唯一变更位置

以下是**可读伪代码**，不是已经测试或可直接覆盖生产源码的实现。实际必须以原项目factory、Tensor布局与provider接口匹配，保持真实Mamba和已有LQI decoder。

```python
# D-only condition, no target G or scoring mask in forward.
# S: [B, 256, 3], F: [B, 256, 384], z: [B, 1024]

def make_trace_anchors(D_norm, S, fixed_U, arm):
    if arm == "G2_Sobol8":
        lo = D_norm.amin(dim=1, keepdim=True)   # [B,1,3]
        hi = D_norm.amax(dim=1, keepdim=True)
        A = lo + (hi - lo) * fixed_U[None]       # [B,256,3]
    elif arm == "G3_MemoryAnchor8":
        A = S                                    # [B,256,3], D-only
    else:
        raise ValueError("unknown research arm")
    return A


def trace_coarse(D_norm, S, F, z, fixed_U, H, arm):
    A = make_trace_anchors(D_norm, S, fixed_U, arm)
    idx = knn_indices(reference=S, queries=A, k=8, stable_ties=True)
    F_norm = layer_norm_per_memory_token(F, affine=False, eps=1e-5)
    picked_F = gather_memory(F_norm, idx)   # [B,256,8,384]
    picked_S = gather_memory(S, idx)        # [B,256,8,3]
    d = picked_S - A[:, :, None, :]
    mu = d.mean(dim=2)                     # [B,256,3]
    rho = d.norm(dim=-1).mean(dim=2, keepdim=True)
    tau = ((d-mu[:, :, None, :]).square().sum(-1).mean(2, keepdim=True)+1e-6).sqrt()
    f = picked_F.mean(dim=2)               # [B,256,384]
    x = torch.cat((z[:, None].expand(-1, 256, -1), f, A, mu, rho, tau), dim=-1)
    assert x.shape[-1] == 1416
    Q = H(x)                               # [B,256,3]; not A + delta
    return Q, {"A": A, "idx": idx, "x": x}

# G0: unchanged original 1024->1024->768 initial coarse head.
# All arms: same original mlp_query, LQI Mamba decoder, FC, and original loss.
```

**注意**：代码中`stable_ties=True`只是需在生产KNN provider中实现或验证的固定数学合同，不是任意假设其已有这个命名参数；若实际API不接受，不得照搬。生产源码应显式核对真实索引和原本的tie行为。示意`LayerNorm`亦需与原冻结实现同字节/同dtype输出对应。

---

## 15. 执行检查清单

- [ ] SPCG原报告、六checkpoint哈希、代码/配置/预测/评分器与资产清单已恢复核对；无臆测的路径或权重文件。
- [ ] 前置规则已冻结：40例fold/type/source、哈希选样、D0指标与预算GO/NO-GO。
- [ ] D0原Q/P至少按冻结合同复现；真实S/F/z/A/N及描述子已实际保存并通过独立计算核验。
- [ ] D0结果明确区分已曝光压力与哈希案例；没有新GT参与任何推理。
- [ ] 仅在D0 GO后，G3公式/唯一接口、参数量、置换行为与KNN自身邻居规则全部冻结。
- [ ] CPU数学测试、原生CUDA最小准入和Tensor消费者/梯度合同通过。
- [ ] 同fold三臂初态与完整batch顺序证据可比；G2/G3设备严格匹配，无跨设备历史值拼表。
- [ ] 禁用SCQ/RF/DAC/额外loss、恢复BN等历史机制；8k/8k/256/3900步/原评分器未变。
- [ ] 预测阶段同次保存Q/P与机制字段，未因存储问题静默删字段。
- [ ] 来源等权E/J与双向距离、类型分层、严重风险新增/挽回和2000次来源Bootstrap全部报告。
- [ ] 结果不满足联合晋级规则时正式收束，不能继续换Sobol种子、扫k、挑seed或后验移除困难病例。
- [ ] checkpoint实际字节的离线备份/恢复状态单独核验；不把报告生成视为GitHub推送、数据上传或服务器清理授权。

---

## 附录 A：关键文献和正式访问入口（截至2026-11-17）

1. Li, Y., Yang, W., Fei, B., **3DMambaComplete: Exploring Structured State Space Model for Point Cloud Completion**，arXiv:2404.07106；后续ACM TOMM 2026版标题为 *3DMambaComplete: Structured State Space Model for High-Efficiency Point Cloud Completion*. https://arxiv.org/abs/2404.07106 ; https://doi.org/10.1145/3774887
2. Fu, Z., et al., **CompletionMamba: Taming State Space Model for Point Cloud Completion**, IEEE TIP 34 (2025), DOI 10.1109/TIP.2025.3597041. https://doi.org/10.1109/TIP.2025.3597041
3. Li et al., **DAPointMamba: Domain Adaptive Point Mamba for Point Cloud Completion**, AAAI 2026. https://ojs.aaai.org/index.php/AAAI/article/view/37596
4. Wu et al., **FusionMamba: Efficient 3D Point Cloud Completion via Spatially-Aware State Space Models and Multi-Scale Information Fusion**, Information Fusion 134:104378, 2026. https://doi.org/10.1016/j.inffus.2026.104378
5. Li et al., **Hyper-PCN: Hypergraph-Based Point Cloud Completion via High-Order Correlation Modeling**, CVPR 2026. https://openaccess.thecvf.com/content/CVPR2026/html/Li_Hyper-PCN_Hypergraph-Based_Point_Cloud_Completion_via_High-Order_Correlation_Modeling_CVPR_2026_paper.html
6. **GDPNet: A Geometry Aware Dual-Path Network for Point Cloud Completion**, 2026. https://www.sciencedirect.com/science/article/pii/S0097849326001810
7. Kwarciak & Wodzinski, **MedPCFM: Improving Medical Point Cloud Completion by Integrating Point Transformers and Flow Matching**, arXiv:2606.24433 (2026). https://arxiv.org/abs/2606.24433
8. Kwarciak & Wodzinski, **MedPCFM-TED: One-Step Point Cloud Flow Matching for Implant Generation via Teacher-Guided Endpoint Distillation**, MICCAI 2026 SASHIMI. https://papers.miccai.org/miccai-2026-sat/SASHIMI_017.html
9. Wodzinski et al., **High-Resolution Cranial Defect Reconstruction by Iterative, Low-Resolution, Point Cloud Completion Transformers**, MICCAI 2023. https://arxiv.org/abs/2308.03813
10. Wodzinski et al., **Automatic Skull Reconstruction by Deep Learnable Symmetry Enforcement**, CMPB 263:108670, 2025. https://doi.org/10.1016/j.cmpb.2025.108670
11. Kodym et al., **SkullBreak / SkullFix – Dataset for Automatic Cranial Implant Design and a Benchmark for Volumetric Shape Learning Tasks**, Data in Brief 35:106902, 2021. https://www.sciencedirect.com/science/article/pii/S2352340921001864
12. Fishman et al., **Thickness and Design Features of Clinical Cranial Implants—What Should Automated Methods Strive to Replicate?**, IJCARS 2024. https://pubmed.ncbi.nlm.nih.gov/38430381/
13. Pathak et al., **Revisiting Point Cloud Completion: Are We Ready for the Real-World?**, ICCV 2025. https://openaccess.thecvf.com/content/ICCV2025/html/Pathak_Revisiting_Point_Cloud_Completion_Are_We_Ready_For_The_Real-World_ICCV_2025_paper.html
14. 用户此前82篇整理中尚待逐一核验全文/正式版本的 SymmCompletion、StruMamba3D、GenPC、PCDreamer、RDS-Net 等，**只列为后续核查线索，不把标题清单冒充已读代码和独立创新性证明**。

## 附录 B：本项目证据与计划的分界

- **历史观察**：数值来自用户上传的《Cranial_BCSP_FullMamba_BCSP_SPCG_完整实验报告_zh_v1.md》（2026-11-17），以及此前SCQ-B/S、RF、DAC、RIVE正式报告。本文没有从这些报告的`E:/`或服务器路径重新读取checkpoint/原始NPZ。
- **本轮网络事实**：外部论文已可定位正式来源；列出的具体摘要主题以出版社/会议/arXiv为准，不以网上解读替代技术实现核验。
- **新计划假设**：BCSP-TRACE、D0的40例采集、G3锚点生成、所有新的训练和性能结果均**尚未执行**；本文件不包含任何预测分数、模型成功声明或背景运行授权。
- **医学边界**：BCSP合成体积缺损中的完整`∂G`与临床真实植入体外表面/厚度/边缘设计不同。必须分别验证点云补全、闭合实体和制造安全，不得混用评价概念。

---

**最终决策**：**先做 D0，不直接启动 G3 的六run。** 如果实际证据不能支持“探针空间支撑不足”与已观察失败的联系，本轮以诊断阴性/不确定收束；如果支持，再以G3相对G2的**同k、同容量、同设备**比较检验Memory锚点生成是否改善真正的完整骨块，而不是继续重复“局部信息更多/半径更好/部分Cover提升”的不可晋级结果。
