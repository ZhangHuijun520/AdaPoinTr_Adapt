# Cranial-BCSP-FullMamba SCQ-F · Fold C／D 复现实验报告

**结题日期**　2026-11-23（北京时间）  
**训练种子**　2026112101  
**阶段结论**　Fold D 复现及八项裁决已完成。现有 F 候选收束，第二种子未进入执行。

## 摘要

本实验检验 SCQ-PRIME 中固定投影臂 F 相对原 FullMamba-LQI 基线 B 的整体路径增益，能否在保持模型实现、初始化规则、训练预算和设备条件一致的前提下，从 Fold C 重现到 Fold D。两折各使用 63 个训练来源、315 个训练病例，以及 21 个开发来源、105 个开发病例。以缺失骨块的自由表面覆盖、共享切壁吻合和预测远端离群联合评估。

Fold C 中，F 相对 B 的来源等权 E P95 降低 **3.654 mm**，严重病例从 **18 例降至 4 例**。Fold D 中，F 的切壁 J Cover@2 提高 **5.476 个百分点**，但 E P95 增加 **0.660 mm**，反向 A2 P95 增加 **5.154 mm**，新增 **6 例严重病例**。Fold D 八项预注册门槛只通过两项。因此，本轮支持 **接口覆盖改善在两折均出现**，整体补全收益与尾部可靠性未达到跨折复现要求。 [Fold C 结题记录][cclose] · [Fold D 正式裁决][dgate]

## 1. 实验目的与证据沿革

1. **复核一个可验证的训练增量。** Fold C 的 F 相对 B 显示了整体覆盖、切壁和风险尾部的同步改善。将原样 F 与同格重新训练的 B 一起放到预定 Fold D，验证收益是否依赖某个开发折及其训练来源组合。
2. **检验局部收益是否伴随全局代价。** 同时报告参考面到预测的覆盖误差、预测到参考面的反向尾部，以及病例严重状态。切壁覆盖提升与其他区域出现离群点在几何上可以同时发生。
3. **将路径利用与模型增益分别检验。** 在历史六例同权重干预中，错配 F 的局部条件使 E/J P95 各在 5／6 例变差。该证据表明这份已训练 F 在这批病例上对 query–邻域配对敏感。Fold D 新训练对照回答整条 F 路径能否改善未见同折开发来源的问题。 [六例诊断结题][six] · [预注册复现协议][plan]

Fold C 证据来自 SCQ-PRIME 的 B／F／S 三臂实验。S 与 F 等容量，S 将七维固定投影换成真实相对几何。原 PRIME 的 S−F 裁决为 *T1_C_FAIL_STOP*。本轮另立协议，使用原样 F 与 B 在 Fold D 做二臂复现，原三臂裁决继续有效。 [PRIME 完整报告][prime] · [Fold C 原裁决][cgate] · [预注册复现协议][plan]

~~~mermaid
flowchart LR
    accTitle: SCQ-F 跨折复现的证据链
    accDescr: 从 Fold C 的历史候选信号出发，以 Fold D 同 seed 配对训练、统一预测和离线评分验证复现，按预注册条件结题。
    c["Fold C B／F 历史配对"] --> d["Fold D B／F 同 seed 配对训练"]
    d --> p["105 例 × 2 臂 Native 预测"]
    p --> s["统一 CPU 评分与只读冻结"]
    s --> g["八项门槛裁决"]
    g --> z["现有 F 候选收束"]
~~~

## 2. 实验内容与方法

### 2.1 模型对照与预测目标

| 臂 | 内容 | 可训练参数 |
| --- | --- | ---: |
| B | FullMamba-LQI。保留 decoder 的原生局部读取、粗点传播与 FC 密集输出 | 39,903,169 |
| F | 在同一母版上增加 SCQ 局部条件残差路径。256 个初始粗点各查 8 个 Memory 邻居，聚合归一化局部特征的 mean、max 及固定七维投影，经 1802→384→3 的 GELU 头生成残差 | 40,596,676 |

F 使用 \(Q_{\mathrm{used}} = Q_{\mathrm{raw}} + \delta\)。\(Q_{\mathrm{used}}\) 进入后续 LQI 原生查询与跨 Memory 取邻，最终经 FC 生成密点。新头末层零初始化，故首步 \(\delta=0\)。Fold D 共 3899 条后续批次几何记录出现非零残差，表明训练后的路径确有输出。F 比 B 多 693,507 个参数，读出、投影、残差和下游坐标传播共同构成受检增量。 [冻结协议][plan] · [Fold D F 训练冻结][df]

### 2.2 数据、配对训练与运行控制

- 数据为 SkullBreak BCSP-GeoV1，采用 V1 暴露体素面物理面积采样。输入是残骨的完整边界 \(\partial D\)，目标是缺失实体骨块的完整边界 \(\partial G\)，包括自由表面 E 及共享切壁 J。输入和输出各 8192 点，输出由 256 个粗点及每个粗点对应的 32 个子点组成。
- 每折按 canonical 来源分离训练与开发。每个来源包含 bilateral、frontoorbital、parietotemporal、random_1、random_2 五类缺损。在冻结 split 中，C／D 开发来源无交集，各折的 21 个开发来源均出现在另一折的训练集合，两折训练共有 42 个来源。每个模型只在自己对应的开发折评价。跨折比较衡量更换训练与开发来源组合后的效果变化。
- 每臂 batch 8，100 次遍历，每次 39 个完整批次。每臂 **3900 次更新、31,200 次病例曝光、300 个尾批丢弃槽**。B／F 在各折内共享初态及实际批次顺序。四个运行的共有参数初态摘要一致，F 在两折的完整参数／持久状态初态摘要也分别一致。
- 沿用 coarse＋dense Chamfer、AdamW、学习率与 BN 调度、FP32，TF32／AMP 关闭。两折四个训练运行的回执记录同一 RTX 4090 D UUID、驱动 570.190。已知 CUDA 梯度存在有限的非位级确定性，证据支持相同执行合同下的对照。每臂固定使用第 99 epoch、3900 步的末步 checkpoint。 [训练与数据协议][plan] · [C-B][cb] · [C-F][cf] · [D-B][db] · [D-F][df]

### 2.3 Native 预测、统一评分与统计

Fold C 历史运行保存 B/F/S 共 315 次 Native 预测及 525 行评分，其中 B/F 各 105 例。Fold D 保存 B/F 共 **210 次 Native forward**，batch 1、FP32、eval、零更新。审计核验两臂预测前后模型与 RNG 指纹一致，记录了实际 coarse、Dense，F 还保存 \(Q_{\mathrm{raw}}\)、\(\delta\)、\(Q_{\mathrm{used}}\)。Fold D 独立 CPU 评分只生成 210 行新模型评分，复用 210 行既有 Nop_D 和 GT_8192 对照记录。 [Fold C 评分冻结][cscore] · [Fold D 预测冻结][dpred] · [Fold D 评分冻结][dscore]

使用残骨包围盒给出的 D-only 中心和尺度反归一化到原世界毫米坐标，保持预测位置参与计分。A1 使用暴露面中心和面面积权重，A2 用面内离散点表达反向最近邻参考。实验使用以下指标。

| 指标 | 含义 |
| --- | --- |
| E P95 | 自由表面 E 到预测点的面积加权第 95 百分位距离，越小越好 |
| J P95 | 共享切壁 J 到预测点的面积加权第 95 百分位距离，越小越好 |
| J Cover@2 | J 的面积加权覆盖率，距离 ≤2 mm 计入，越大越好 |
| 反向 A2 P95 | 预测点到 A2 参考面的距离 P95，越小越好 |
| far20 | 预测到 A2 距离严格大于 20 mm 的点占比，越小越好 |
| 严重事件 | 病例满足 E P95 >20 mm 或 J Cover@2 =0 |

先在同一病例计算 F−B，再对同一来源的五类缺损等权，随后对 21 个来源等权。两折各使用 2,000 次来源级配对 bootstrap 估计 95% 百分位区间，Fold D 按冻结 PCG64 种子 2026112303，并核对逐来源留一范围。区间反映固定训练结果下的开发来源不确定性。八项门槛使用未舍入结果，区间用于证据解释。 [指标与判定协议][plan] · [Fold C 配对汇总][cpairs] · [Fold D 配对汇总][dpairs]

## 3. 实验结果

### 3.1 两折整体结果

表中 Δ 为 F−B。覆盖率和离群比例的差值以百分点计。各均值来自冻结的来源等权汇总。

| 指标 | Fold C B | Fold C F | Fold C Δ | Fold D B | Fold D F | Fold D Δ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| E P95（mm） | 11.349 | 7.695 | −3.654 | 9.335 | 9.995 | +0.660 |
| J P95（mm） | 14.446 | 10.577 | −3.869 | 13.428 | 13.328 | −0.100 |
| J Cover@2（%） | 43.085 | 51.117 | +8.031 | 39.027 | 44.503 | +5.476 |
| 反向 A2 P95（mm） | 14.248 | 10.861 | −3.387 | 9.323 | 14.477 | +5.154 |
| far20（%） | 7.831 | 3.831 | −4.000 | 3.509 | 7.267 | +3.758 |
| 严重病例（例） | 18 | 4 | −14 | 10 | 11 | +1 |

| F−B 指标 | Fold C 95% 来源区间 | Fold D 95% 来源区间 | C／D 改善来源数 |
| --- | ---: | ---: | ---: |
| E P95（mm） | [−5.371, −1.969] | [−1.025, +2.306] | 18／21 · 13／21 |
| J P95（mm） | [−5.682, −2.010] | [−1.908, +1.708] | 18／21 · 13／21 |
| J Cover@2（百分点） | [+5.295, +10.684] | [+1.308, +9.347] | 19／21 · 16／21 |
| 反向 A2 P95（mm） | [−5.080, −1.747] | [+2.725, +7.297] | 16／21 · 1／21 |
| far20（百分点） | [−6.424, −1.755] | [+0.040, +7.113] | 15／21 · 4／21 |

Fold D E P95 在 13 个来源改善，但等权均值增加 0.660 mm，说明改善与回退的幅度不对称。逐一剔除任一来源，E P95 平均差仍在 **+0.324 至 +0.979 mm**，表明删除一个来源不足以使该平均差转向改善。该敏感性检查与 bootstrap 回答不同问题，E P95 的来源级 95% 区间仍跨零。 [C 折配对结果][cpairs] · [D 折配对结果][dpairs] · [D 折裁决][dgate]

### 3.2 Fold D 八项冻结裁决

| 指标 | 实测 | 门槛 | 结果 |
| --- | ---: | ---: | --- |
| E P95 差（mm） | +0.660 | ≤ −0.50 | 未通过 |
| E P95 改善来源 | 13／21 | ≥ 14／21 | 未通过 |
| J P95 差（mm） | −0.100 | ≤ +0.25 | 通过 |
| J Cover@2 差（百分点） | +5.476 | ≥ −0.50 | 通过 |
| 反向 A2 P95 差（mm） | +5.154 | ≤ +0.50 | 未通过 |
| far20 差（百分点） | +3.758 | ≤ +0.25 | 未通过 |
| 严重病例总数 | F 11，B 10 | F ≤ B | 未通过 |
| F 新增严重 | 6／105 | ≤ 2／105 | 未通过 |

八项均通过才进入下一阶段的收益与成本审阅。当前仅通过两项，状态为 *STOP_ADDITIONAL_CANDIDATE_RUNS_UNDER_PREREGISTERED_RULE*。E P95 的区间跨零影响其效果估计的解释，协议的收束由预先锁定的收益与风险阈值决定。 [预注册协议][plan] · [正式裁决][dgate]

### 3.3 缺损类型和严重病例转移

每折每类 21 例。表中按缺损类型描述 F−B，未做额外的类型级检验。

| 缺损类型 | C E P95（mm） | D E P95（mm） | D J Cover@2（百分点） | D 反向 A2 P95（mm） |
| --- | ---: | ---: | ---: | ---: |
| bilateral | −1.242 | −1.632 | +18.090 | +3.797 |
| frontoorbital | −13.044 | +6.548 | −7.304 | +9.412 |
| parietotemporal | +0.228 | +1.177 | +6.491 | +8.096 |
| random_1 | −2.303 | −1.674 | +4.088 | +2.629 |
| random_2 | −1.909 | −1.120 | +6.014 | +1.837 |

Fold C 的整体改善很大一部分来自额眶缺损，Fold D 同类方向反转。Fold D 五类的反向 A2 P95 差值均为正。双侧和两类随机缺损仍有较好的平均 E P95，并同时出现反向距离回退，说明反向风险值得单独保留。 [两折冻结类型汇总][cpairs] · [Fold D 类型汇总][dpairs]

| 折 | B 严重 | F 严重 | F 新增严重 | F 挽回 | 双臂共同严重 |
| --- | ---: | ---: | ---: | ---: | ---: |
| C | 18 | 4 | 1 | 15 | 3 |
| D | 10 | 11 | 6 | 5 | 5 |

Fold D 新增严重病例的错误并不完全相同。下列为冻结分数的病例差值。正的 far20 表示预测中的远端点占比上升。

| Fold D 新增病例 | Δ E P95（mm） | Δ J Cover@2（百分点） | Δ 反向 A2 P95（mm） | Δ far20（百分点） |
| --- | ---: | ---: | ---: | ---: |
| train__010__frontoorbital | +37.72 | −41.66 | +44.99 | +85.91 |
| train__022__random_1 | +24.21 | −24.73 | +44.75 | +50.98 |
| train__060__bilateral | +23.90 | +11.68 | +0.17 | 0.00 |
| train__062__frontoorbital | +27.14 | −25.37 | +36.32 | +68.92 |
| train__068__frontoorbital | +19.74 | −25.69 | +24.26 | +50.89 |
| train__093__parietotemporal | +40.48 | −49.60 | +45.81 | +91.33 |

六例中五例出现大幅反向退化。双侧病例 *train__060__bilateral* 的 far20 无变化且切壁覆盖上升，E P95 却明显回退，符合另一种表面覆盖失效表现。Fold D 五个挽回病例为 *train__004__random_2*、*train__008__random_2*、*train__062__random_1*、*train__069__parietotemporal* 与 *train__079__parietotemporal*。最后一例虽退出预定义严重状态，反向 A2 P95 和 far20 仍分别增加约 37.06 mm 与 41.27 个百分点，说明严重状态与反向尾部应联合观察。 [完整病例差值][dpairs] · [严重转移名单][dgate]

### 3.4 Fold D 推理成本

使用同一次 Native 预测的同步时延。每臂前五例保留预测并排除于计时分位数，余下每臂 100 例统计输入已上设备至 Dense 同步完成的时间。

| 臂 | P50（ms） | P95（ms） | 峰值分配显存（MiB） | 峰值预留显存（MiB） |
| --- | ---: | ---: | ---: | ---: |
| B | 47.68 | 51.87 | 229.91 | 268.00 |
| F | 49.12 | 55.29 | 232.56 | 268.00 |

F／B 的 P50 比为 1.030，峰值分配显存比为 1.012。观测成本低于协议的 1.50 复核触发线，本轮决策由补全收益和尾部风险门槛决定。Fold C 历史运行没有与本次一致的逐例同步时延记录，仅报告 Fold D 的同口径成本。 [推理冻结回执][dpred]

## 4. 结果分析、出现的问题和证据边界

**接口覆盖的重复改善具有明确范围。** 两折 J Cover@2 的 F−B 方向一致，两个来源级区间均位于零以上。Fold D 的 J P95 接近持平，区间跨零。覆盖率达到 2 mm 的切壁面积可以增加，同时仍有切壁位置存在较大误差。该发现支持进一步理解局部条件如何改变切壁覆盖，现有点云指标无法判定临床植入吻合。

**整体覆盖和反向精度未同步复现。** Fold D 的 E P95 没有达到预设改善，反向 A2 P95 增加超过 5 mm，21 个来源中仅 1 个在该反向指标改善。在同一份预测中，点可能更密集地支撑部分切壁，同时点集的另一部分远离真实骨块。正反向指标的组合与这种误差分布相符，具体几何表现仍需看已保存的病例。现有汇总还无法区分整体偏移、局部缺点和少量远端簇的分别作用。

**路径失效所在阶段仍待定位。** Fold D 观察到远端离群和严重例换位，但尚未逐病例比较 B 的 coarse／Dense 与 F 的 \(Q_{\mathrm{raw}}\rightarrow Q_{\mathrm{used}}\rightarrow\mathrm{Dense}\)。因此无法判断退化是否首次出现在残差修正，或由后续查询、传播或子点生成放大。六例错配实验提供的是 Fold C 已训练权重的条件响应证据，无法据此定位 Fold D 的失效阶段。 [六例干预结题][six] · [Fold D 病例级评分][dcases]

**模型对照与外推范围有限。** F−B 同时改变局部读取、固定投影、残差及坐标传播，并增加参数量。即使某些指标改善，也需要独立的容量和功能对照才能归因到某一组件。两折采用同一训练种子，开发来源互斥但训练来源重叠。Fold C 又承担候选发现作用，Fold D 在本轮承担独立于该发现的预注册裁决。按折呈现结果，避免用两折简单汇总覆盖 Fold D 的尾部回退。结论仅覆盖 SkullBreak 的已开放合成缺损、既定表示和模型版本，尚无跨 seed、独立测试集或临床来源证据。 [复现协议][plan] · [Fold C 原裁决][cgate] · [Fold D 正式裁决][dgate]

**执行中出现的两个工程问题已区分处理。** Fold D 开发输入实际位于目录名含 *foldc* 的现有数据目录。发现在旧入口锁定目录中找不到首个开发病例后，按冻结病例清单重新核验全部 105 份输入的路径、大小和 SHA256，只修正根路径绑定，保持病例集合、顺序和坐标口径。首轮预测后审计因本机 Python 3.9 不支持 *zip(strict=True)* 中止，随后以显式长度相等检查保留原审计要求并完成新版本只读审计。评分、汇总和裁决均以通过正式审计的证据为准。 [输入路径回读][path] · [预测冻结审计][dpred] · [评分冻结审计][dscore]

## 5. 正式结题及后续研究边界

结题裁决为 **停止追加当前 F 候选的训练**。Fold D 没有复现预注册要求的整体补全收益及尾部安全性，接口覆盖改善作为单独的机制线索保留。后续如需归因，可直接利用已冻结的 6 个新增严重病例和 5 个挽回病例，在同一世界坐标下比较 B／F 粗点、F 的残差后粗点和最终 Dense。若离群在 \(Q_{\mathrm{used}}\) 阶段已出现，优先检验残差的空间支撑。若离群主要在 Dense 阶段放大，优先核查父点和子点的传播与覆盖。若现有产物无法区分两者，登记未决。该归因未在本轮报告中执行。 [预注册裁决][dgate] · [冻结预测归档回执][dpred]

本报告冻结既有实验结果与可核验的证据索引。以下摘要来自正式回执，checkpoint 行记录训练终点字节指纹。

| 终点 | 字节数 | SHA256 |
| --- | ---: | --- |
| B_C | 478,810,547 | 1d61d62764d7ac0354b86e73c4228bad13072c85ba01cb9cc3bd726624b0e4e0 |
| F_C | 487,148,514 | 65e370e698e191c4715130b1fce01ebec61000d845812cd4b2a4ba7983a84a7e |
| B_D | 478,810,547 | fa033cbffbed813f9f084dd109101ca672ad9594473c14652f95fac2897a49cf |
| F_D | 487,148,514 | 4b94cf10a724423bf93e43ab430a44cfafb6448b2373ee974de3e602895eb4ca |

Fold C 的原始预测归档覆盖三臂，大小 **30,715,098 字节**，SHA256 为 *3ce5c5906a301d3672458b7fc0b6fcdb4a0a187e27a333265534fea4486b463c*。Fold D 两臂归档大小 **20,587,529 字节**，SHA256 为 *8ad3308467008e2609018648b9b859561c8a29b7c238df0d53d9e3b37bb7d802*。本机证据清单记录报告、协议、训练与预测回执、评分、裁决及实际存在的本机证据文件的字节数和 SHA256。权重在本报告中以正式回执记录的终点指纹为准。 [本机证据清单][manifest] · [C 折预测冻结][cpred] · [D 折预测冻结][dpred]

[plan]: SCQ-F_FoldD_BF_两臂复现协议_2026-11-23_v1.md
[six]: SCQ-F_六例冻结权重诊断_结题记录_2026-11-23_v1.md
[prime]: Cranial_BCSP_FullMamba_SCQ_PRIME_完整实验报告_zh_v1.md
[cclose]: ../../outputs/scq_prime_foldC_training_preparation_20261122_v1/SCQ_PRIME_T1-C_结题记录_zh_v1.md
[cgate]: ../../outputs/scq_prime_foldC_training_preparation_20261122_v1/BFS_C_cpu_scoring_preparation_v1/BFS_C_T1C_preregistered_gate_v1.json
[cb]: ../../outputs/scq_prime_foldC_training_preparation_20261122_v1/B_C_post_training_freeze_v1/B_C_post_training_freeze_receipt_v1.json
[cf]: ../../outputs/scq_prime_foldC_training_preparation_20261122_v1/F_C_post_training_freeze_v1/F_C_post_training_freeze_receipt_v1.json
[cpred]: ../../outputs/scq_prime_foldC_training_preparation_20261122_v1/BFS_C_native_prediction_preparation_v1/post_prediction_freeze_v2/BFS_C_post_prediction_freeze_receipt_v1.json
[cscore]: ../../outputs/scq_prime_foldC_training_preparation_20261122_v1/BFS_C_cpu_scoring_preparation_v1/BFS_C_post_scoring_freeze_audit_v1.json
[cpairs]: ../../outputs/scq_prime_foldC_training_preparation_20261122_v1/BFS_C_cpu_scoring_preparation_v1/unified_scores_v1/paired_comparisons.json
[db]: ../../outputs/scq_fv_20261122_v2/foldD_BF_B_D_request_preparation_v1/B_D_post_training_freeze_v1/B_D_post_training_freeze_receipt_v1.json
[df]: ../../outputs/scq_fv_20261122_v2/foldD_BF_F_D_request_preparation_v1/F_D_post_training_freeze_v1/F_D_post_training_freeze_receipt_v1.json
[dpred]: ../../outputs/scq_fv_20261122_v2/foldD_BF_native_prediction_pending_v2/post_prediction_freeze_v2/BF_D_post_prediction_freeze_receipt_v1.json
[path]: ../../outputs/scq_fv_20261122_v2/foldD_BF_native_prediction_pending_v1/BF_D_native_development_path_readback_v2.json
[dscore]: ../../outputs/scq_fv_20261122_v2/foldD_BF_cpu_scoring_preparation_v1/BF_D_post_scoring_freeze_audit_v1.json
[dpairs]: ../../outputs/scq_fv_20261122_v2/foldD_BF_cpu_scoring_preparation_v1/unified_scores_v1/paired_comparisons.json
[dcases]: ../../outputs/scq_fv_20261122_v2/foldD_BF_cpu_scoring_preparation_v1/unified_scores_v1/case_metrics.jsonl
[dgate]: ../../outputs/scq_fv_20261122_v2/foldD_BF_cpu_scoring_preparation_v1/BF_D_eight_gate_decision_v1.json
[manifest]: ../../outputs/scq_fv_20261122_v2/SCQ_F_CD_replication_evidence_manifest_v1.json
