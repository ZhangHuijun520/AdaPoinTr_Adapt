# 颅骨缺损点云补全实验评价协议

## 1. 目的与结论

本文档用于固定 AdaPoinTr/Mamba 颅骨缺损补全实验的评价口径，避免在实验完成后再选择有利指标。

核心原则：

1. **主要评价对象是预测植入物/缺损区域，而不是完整颅骨。**
2. **所有几何距离在患者物理坐标系中计算，单位为 mm。**
3. 同时评价体积重叠、整体表面、极端表面误差和点云几何，不能只报告单一指标。
4. 训练时的归一化坐标只用于网络输入；评价前必须恢复到原始 NRRD 世界坐标。
5. 主结果按病例做宏平均，不把所有体素或点拼接后计算一个总分。
6. 所有模型使用完全一致的植入物提取、网格化、体素化和后处理流程。

建议的最终指标体系如下。

### 1.1 主质量指标

| 指标 | 方向 | 单位 | 评价对象 | 作用 |
|---|---:|---:|---|---|
| Implant DSC | ↑ | 无 | 植入物体素掩膜 | 与 SkullFix、SkullBreak 和 AutoImplant 文献直接比较 |
| AutoImplant bDSC | ↑ | 无 | 缺损边缘邻域内的植入物掩膜 | 衡量植入物在骨窗边缘附近的局部重叠 |
| NSD / Surface Dice@1 mm | ↑ | 无 | 植入物完整表面 | 衡量落入 1 mm 容差内的表面积比例 |
| HD95 | ↓ | mm | 植入物完整表面 | 衡量较严重但排除最极端离群点的表面偏差 |
| Symmetric CD-L1 | ↓ | mm | 植入物表面点云 | 与点云补全文献和目标论文比较 |

### 1.2 任务特异与诊断指标

| 指标 | 方向 | 单位 | 建议级别 |
|---|---:|---:|---|
| ASSD | ↓ | mm | 辅指标 |
| Implant Precision / Recall | ↑ | 无 | 辅指标，分别反映越界材料与缺损覆盖 |
| signed RVE / absolute RVE | →0 / ↓ | % | 辅指标 |
| Rim-ASSD / Rim-HD95 | ↓ | mm | 任务特异指标，完成稳定性验证后使用 |
| DCD | ↓ | 无 | 点云密度诊断指标 |
| Point F-score@1 mm | ↑ | 无 | 点云文献兼容指标，建议放附录 |
| 有效植入物率、连通分量、最大分量占比 | ↑ / ↓ / ↑ | 无 | 失败模式与可制造性诊断 |

### 1.3 效率指标

| 指标 | 方向 | 报告要求 |
|---|---:|---|
| Params | ↓ | M，统计可训练参数和总参数 |
| MACs/FLOPs | ↓ | G，注明输入点数、输出点数、统计工具和自定义算子覆盖情况 |
| Inference latency | ↓ | s/case，batch=1，报告 median、IQR 和 p95 |
| Peak inference GPU memory | ↓ | GB，batch=1，单病例，清空峰值后测量 |
| Throughput | ↑ | cases/s，可作为补充 |
| Peak training memory / time per epoch | ↓ | 与推理效率分表报告 |

若论文版面有限，主文表格优先保留 DSC、bDSC、NSD@1 mm、HD95、CD-L1、Params、Latency 和 Peak Memory；其余放消融或补充材料。

## 2. 评价对象

每个病例至少保存下列对象：

- `S_def`：缺损颅骨。
- `S_gt`：完整颅骨。
- `I_gt`：真实缺失区域或参考植入物。
- `I_pred_pc`：网络直接输出的植入物点云。
- `I_pred_mesh`：统一网格化后的预测植入物。
- `I_pred_voxel`：映射回原始图像网格后的预测植入物掩膜。

必须优先直接使用数据集提供的 implant 标签。若需要从完整颅骨与缺损颅骨推导，应统一使用：

```text
I_gt = S_gt AND NOT S_def
```

预测完整颅骨时，预测植入物应使用固定流程从预测完整颅骨中提取，不允许针对不同模型手工修补。

完整颅骨指标只能作为数据管线检查或补充结果。由于绝大部分健康颅骨区域没有变化，完整颅骨 DSC/CD 会稀释缺损区域误差，不能作为主要结论依据。

## 3. 坐标、单位与重采样

### 3.1 物理坐标

点 `v = [i, j, k, 1]^T` 应通过 NRRD/DICOM 仿射矩阵映射为：

```text
x_world = A @ v
```

所有 CD、ASSD、HD95、NSD 容差和 rim 距离均在 `x_world` 中计算。

如果训练前采用了中心化和尺度归一化：

```text
x_norm = (x_world - center) / scale
```

评价前必须使用同一病例保存的 `center` 和 `scale` 还原：

```text
x_world = x_norm * scale + center
```

不得用归一化坐标中的 `0.01` 冒充 `1 mm`。

### 3.2 体素指标

DSC、bDSC、Precision、Recall 和 RVE 在统一物理网格上计算。首选原始病例网格及原始 spacing、origin、direction。若不同方法输出分辨率不同，统一用最近邻插值重采样二值掩膜。

可在补充材料增加固定 1 mm 各向同性网格的敏感性实验，但主结果不得混用不同网格。

### 3.3 表面指标

表面指标必须考虑各向异性 spacing。推荐从体素掩膜提取物理表面单元并按实际表面积加权，或使用经过验证的 surface-distance 实现。简单把每个边界体素计为同等面积，会在各向异性 CT 上产生系统偏差。

## 4. 主质量指标定义

### 4.1 Implant DSC

对预测植入物体素集合 `P` 和真实植入物集合 `G`：

```text
DSC = 2 |P ∩ G| / (|P| + |G|)
```

DSC 是领域可比性最强的重叠指标，但对结构形状和误差距离不敏感，因此必须与表面指标联合报告。

空集合规则：

- `P` 和 `G` 都为空：该病例不适用于当前缺损补全任务，应在数据检查阶段排除。
- `G` 非空而 `P` 为空：DSC=0，并记录为失败病例。

### 4.2 AutoImplant bDSC

AutoImplant 的 bDSC 是在**缺损颅骨边缘附近的局部区域**计算预测植入物与真实植入物的 Dice，关注植入物能否贴合骨窗边缘。

它不等于 Surface Dice。正式实验必须：

1. 使用 AutoImplant 官方实现或经逐例对照验证的等价实现。
2. 固定边缘邻域的构造方法和宽度。
3. 保存官方代码版本、commit 和参数。
4. 在论文中使用 `border DSC (bDSC)`，不要写成 Surface Dice 的别名。

在未验证官方实现前，不应自行定义一个“边界 Dice”并与既有论文数值直接比较。

### 4.3 NSD / Surface Dice@1 mm

设预测和真实表面分别为 `S_P`、`S_G`，表面积为 `|.|`，容差为 `τ`：

```text
NSD@τ =
  (预测表面中距真实表面不超过 τ 的面积
   + 真实表面中距预测表面不超过 τ 的面积)
  / (|S_P| + |S_G|)
```

本项目预注册：

- 主阈值：`τ = 1.0 mm`。
- 敏感性分析：`τ = 0.5 mm` 和 `τ = 2.0 mm`。

1 mm 是当前的工程评价容差，不应在没有外科专家或标注者间变异研究支持时宣称为普适“临床合格阈值”。若后续获得多位专家的 implant 标注，应根据标注者间表面偏差重新确定主阈值。

### 4.4 HD95

先计算两个方向的最近表面距离：

```text
d_PG = { min_y ||x-y||_2 : x ∈ S_P, y ∈ S_G }
d_GP = { min_x ||y-x||_2 : y ∈ S_G, x ∈ S_P }
```

将两个方向的距离合并后取第 95 百分位，单位为 mm。实现时必须固定使用“合并后百分位”还是“双向百分位取最大值”，二者不能混用。

本项目建议采用经验证库的对称 HD95 定义，并在方法部分注明库名和版本。最大 HD 对单个噪点过于敏感，只在补充材料中报告。

### 4.5 Symmetric CD-L1

对从预测和真实植入物表面进行**面积均匀采样**得到的点集 `P`、`G`：

```text
CD-L1_mm =
  0.5 * [
    mean_{p∈P} min_{g∈G} ||p-g||_2
    +
    mean_{g∈G} min_{p∈P} ||g-p||_2
  ]
```

注意事项：

- 使用欧氏距离，不平方。
- 单位为 mm。
- 两个方向等权平均。
- 每个表面固定相同采样点数和随机种子。
- 点必须按三角形面积均匀采样，不能直接比较密度不均匀的网络输出。

文献中的 CD 可能使用平方距离、求和而非平均、乘以 `10^3/10^4`，因此论文中必须写出公式，不能只写“CD”。

## 5. 辅助指标

### 5.1 ASSD

ASSD 是两个方向最近表面距离的平均值，单位为 mm。它反映典型表面误差，比 HD95 平滑。

当 CD 使用面积均匀采样、非平方欧氏距离时，CD-L1 与 ASSD 信息高度相近。保留两者的理由是：

- ASSD 对接医学图像表面评价。
- CD 对接点云补全文献。

若版面受限，ASSD 放入补充材料即可。

### 5.2 Precision 和 Recall

```text
Precision = |P ∩ G| / |P|
Recall    = |P ∩ G| / |G|
```

- Recall 对应缺损覆盖完整度。
- Precision 反映预测材料是否越出真实植入物区域。

AutoImplant 临床评审将 completeness 和 false-positive material 视为不同问题；仅用 DSC 会把两类错误混合，因此建议至少在补充表中报告 Precision/Recall。

### 5.3 体积误差

```text
signed_RVE = 100% * (V_pred - V_gt) / V_gt
abs_RVE    = |signed_RVE|
```

同时报告 signed RVE 和 absolute RVE：

- signed RVE 显示系统性过大或过小。
- absolute RVE 显示体积偏差幅度。

RVE 不能判断错误发生的位置，也可能因多预测和少预测相互抵消，不能替代 DSC 和表面指标。

### 5.4 DCD

建议使用原论文名称 `Density-aware Chamfer Distance (DCD)`。上传的颅骨点云论文在正文中写作 DACD，但其引用对应的是 DCD 工作；除非复现代码明确实现了另一种 DACD，不要把两个名称混用。

DCD 可揭示点云局部密度和细节质量，但它：

- 无直接临床单位。
- 对采样策略和超参数敏感。
- 不适合作为单独的医学主指标。

因此建议作为点云质量诊断或消融指标。

### 5.5 Point F-score@1 mm

以双向最近邻距离小于 `τ` 的点比例定义 precision 和 recall，再计算调和平均：

```text
F@τ = 2 * precision_τ * recall_τ / (precision_τ + recall_τ)
```

本项目若报告该指标，固定 `τ=1 mm`，并补充 `0.5/2 mm`。

Point F-score 与 Surface Dice 都是阈值型双向表面匹配指标。前者按点计权且受采样密度影响，后者按表面积计权。主文优先使用 NSD/Surface Dice；F-score 仅用于与点云补全文献比较，避免把两个近似重复指标都包装成独立贡献。

## 6. Rim / interface 贴合指标

边缘贴合对植入物能否放入骨窗非常重要，但自定义指标必须先解决边缘提取的稳定性。

建议定义接触带：

```text
C(I, S_def; δ) =
  { x ∈ surface(I) : distance(x, surface(S_def)) <= δ }
```

其中 `δ=1 mm`。分别得到预测接触带和真实接触带后，计算：

- `Rim-ASSD [mm]`
- `Rim-HD95 [mm]`
- 可选 `Rim-NSD@1 mm`

正式采用前必须完成：

1. 随机可视化至少 20 个病例的真实和预测接触带。
2. 测试 `δ=0.5/1/2 mm` 对排名的影响。
3. 明确接触带为空时的失败规则。
4. 验证存在轻微重叠、间隙和多连通分量时仍能稳定工作。

在上述验证完成前，bDSC 是更适合主文的边缘指标，Rim-ASSD/Rim-HD95 作为探索性分析。

## 7. 有效性和失败模式

每个预测植入物还应检查：

- 是否为空。
- 连通分量数量。
- 最大连通分量体积占比。
- 是否存在明显远离缺损区的分量。
- 网格是否 watertight。
- 是否有自交、退化面或异常孔洞。
- 后处理是否失败。

建议报告：

```text
valid_implant_rate = 有效病例数 / 全部测试病例数
```

失败病例不得从均值中静默删除。主指标按预先定义的最差值或失败规则处理，并单独报告失败率。

## 8. 效率评价协议

所有模型在同一 GPU、CUDA、PyTorch、精度模式和输入规模下测试。

### 8.1 推理时间

- `batch_size=1`
- 至少 20 次 warm-up
- 至少 100 次正式测量或遍历整个测试集
- 每次计时前后执行 `torch.cuda.synchronize()`
- 将数据加载时间、网络时间、后处理时间和总时间分开
- 报告 median、IQR、mean、SD 和 p95

### 8.2 GPU 显存

每次测量前：

```python
torch.cuda.empty_cache()
torch.cuda.reset_peak_memory_stats()
```

报告网络前向峰值和端到端峰值。训练峰值显存必须与推理峰值显存分开。

### 8.3 Params 与 FLOPs

Params 相对稳定；FLOPs/MACs 对 kNN、FPS、Chamfer、自定义 CUDA 和 Mamba scan 的覆盖可能不完整。因此必须同时报告：

- 统计工具和版本。
- 是否包含自定义 CUDA 算子。
- 输入/输出点数。
- MACs 还是 FLOPs，以及二者换算规则。

真实延迟和显存比单独的 FLOPs 更能反映部署成本。

## 9. 汇总与统计检验

### 9.1 病例级汇总

先逐病例计算指标，再进行宏平均：

- `mean ± SD`
- `median [IQR]`
- 95% bootstrap confidence interval

主表可显示 `mean ± SD`，补充材料提供中位数、IQR、CI 和逐病例 CSV。

### 9.2 配对比较

同一测试病例上的模型结果是配对数据。建议：

- 两模型：配对 Wilcoxon signed-rank test 或配对 permutation test。
- 多个消融：Friedman test 后进行配对事后比较。
- 多指标/多比较：Holm 校正。
- 同时报告效应量和 95% CI，不能只报告 p 值。

### 9.3 SkullBreak 的聚类问题

SkullBreak 中同一完整颅骨可对应多个人工缺损，这些样本不是完全独立。数据划分必须按原始颅骨/患者分组，统计时使用：

- 先在每个原始颅骨内平均，再跨颅骨统计；或
- 以原始颅骨为重采样单元做 cluster bootstrap。

禁止把同一颅骨的不同缺损随机拆到训练集和测试集。

### 9.4 分层结果

除总体指标外，建议按以下因素分层：

- 缺损体积：small / medium / large。
- 缺损位置。
- 缺损形态或 SkullBreak 类型。
- 输入点数或缺损比例。

分层阈值必须由训练集或预设规则确定，不能根据测试结果临时调整。

## 10. 公平后处理

点云网络、体素网络和其他基线的原生输出不同。建议同时保存两层评价：

1. **Native representation evaluation**
   - 网络直接输出点云的 CD、DCD、Point F-score。
2. **Common clinical representation evaluation**
   - 所有方法经过同一网格化、体素化和形态学后处理后，计算 DSC、bDSC、NSD、HD95、ASSD 和 RVE。

后处理参数只在训练/验证集上确定并冻结。测试集禁止逐例调参。

建议额外做一项后处理消融，说明性能提升来自模型还是形态学修补。

## 11. 建议的论文表格

### 表 1：主要重建质量

```text
Method | DSC ↑ | bDSC ↑ | NSD@1mm ↑ | HD95(mm) ↓ | CD-L1(mm) ↓
```

### 表 2：临床相关诊断

```text
Method | Precision ↑ | Recall ↑ | ASSD(mm) ↓ |
signed RVE(%) →0 | abs RVE(%) ↓ | Valid rate ↑
```

### 表 3：效率

```text
Method | Params(M) ↓ | MACs/FLOPs(G) ↓ |
Latency median/p95(s) ↓ | Peak memory(GB) ↓
```

### 表 4：缺损分层与鲁棒性

```text
Method | Small | Medium | Large | Defect type/location
```

表 4 至少报告一个重叠指标和一个距离指标，避免只展示单一分数。

## 12. 当前应冻结的决策

在开始 SkullFix 正式 baseline 前，建议锁定以下内容：

- [ ] 主评价对象为 implant，而非 complete skull。
- [ ] 世界坐标恢复和 mm 单位经过人工点位验证。
- [ ] DSC 使用原始网格。
- [ ] bDSC 使用 AutoImplant 官方实现并记录版本。
- [ ] NSD 主阈值为 1 mm，补充 0.5/2 mm。
- [ ] HD95 定义和实现库固定。
- [ ] CD 使用非平方、双向等权、面积均匀采样，单位 mm。
- [ ] ASSD、Precision/Recall、signed/abs RVE 作为辅指标。
- [ ] DCD 和 Point F-score 只作为点云诊断/文献兼容指标。
- [ ] rim 指标完成接触带可视化验证后再进入正式表格。
- [ ] 推理时间和显存的硬件与测量协议固定。
- [ ] 按病例宏平均并保存逐病例 CSV。
- [ ] SkullBreak 按原始颅骨分组划分和统计。
- [ ] 所有模型共享相同后处理。

## 13. 文献依据

1. Wodzinski M, et al. High-Resolution Cranial Defect Reconstruction by Iterative, Low-Resolution, Point Cloud Completion Transformers. MICCAI 2023.
   https://doi.org/10.1007/978-3-031-43996-4_32
2. Li J, et al. Towards clinical applicability and computational efficiency in automatic cranial implant design: An overview of the AutoImplant 2021 cranial implant design challenge. Medical Image Analysis, 2023.
   https://doi.org/10.1016/j.media.2023.102865
3. AutoImplant 2021 Evaluation and Ranking.
   https://autoimplant2021.grand-challenge.org/evaluation_ranking/
4. Ellis DG, et al. Qualitative Criteria for Feasible Cranial Implant Designs. AutoImplant 2021.
5. Reinke A, et al. Metrics Reloaded: Recommendations for image analysis validation. Nature Methods, 2024.
   https://pmc.ncbi.nlm.nih.gov/articles/PMC11182665/
6. Nikolov S, et al. Clinically Applicable Segmentation of Head and Neck Anatomy for Radiotherapy. Journal of Medical Internet Research, 2021.
   https://doi.org/10.2196/26151
7. Wu T, et al. Density-aware Chamfer Distance as a Comprehensive Metric for Point Cloud Completion. NeurIPS 2021.
   https://proceedings.neurips.cc/paper/2021/hash/f3bd5ad57c8389a8a1a541a76be463bf-Abstract.html
8. Yeghiazaryan V, Voiculescu I. Family of boundary overlap metrics for the evaluation of medical image segmentation. Journal of Medical Imaging, 2018.
   https://doi.org/10.1117/1.JMI.5.1.015006

## 14. 当前实现状态

第一阶段毫米制点集评价器位于：

```text
utils/skullfix_metrics.py
```

它已经实现：

- `normalized_to_world`：从 SkullFix 归一化坐标恢复到 NRRD 世界坐标，单位 mm。
- `world_to_normalized`：世界坐标到归一化坐标的逆变换。
- 双向最近邻欧氏距离。
- symmetric CD-L1 [mm]。
- point-sampled ASSD [mm]。
- combined symmetric HD95 [mm]。
- point-sampled NSD@0.5/1/2 mm。

解析合成验证脚本位于：

```text
tools/validate_skullfix_metric_units.py
```

服务器运行：

```bash
cd ~/adapointr_work/PoinTr
conda activate adapointr-server
python tools/validate_skullfix_metric_units.py \
  --data_root data/SkullFixPC
```

验证内容：

1. 完全相同点集必须得到 CD=ASSD=HD95=0 mm，NSD=1。
2. 稀疏立方体整体平移 1 mm，必须得到 CD=ASSD=HD95=1 mm。
3. 同一 1 mm 平移下，NSD@0.5 mm=0，NSD@1/2 mm=1。
4. 人工 centroid/scale 的归一化往返必须恢复原始世界坐标。
5. 真实 SkullFix NPZ 的 normalized-world-normalized 往返误差必须接近机器精度。
6. 真实 NPZ 中的毫米指标必须等于归一化距离乘以病例 scale；NSD 阈值也必须满足相同尺度对应关系。

当前实现是对**采样表面点集**的评价，适用于网络原生点云输出和点云层面的 sanity/overfit 监控。它还不包括：

- 体素 Implant DSC。
- AutoImplant 官方 bDSC。
- 基于完整体素/三角网格表面积加权的精确 Surface Dice。
- 从预测 complete skull 中稳定提取 predicted implant 的正式后处理。

因此，当前 point-sampled NSD/ASSD 不能冒充最终体素/网格评价结果。正式 baseline 前还需要完成共同后处理和体素/表面评价器。
