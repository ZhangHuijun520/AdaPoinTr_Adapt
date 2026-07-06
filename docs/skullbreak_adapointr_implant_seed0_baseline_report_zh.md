# AdaPoinTr-Implant SkullBreak Seed-0 Baseline 完整实验报告

_SkullBreak 数据接入、分组 Gate、全量训练、毫米制点云评估、体素评估与归档记录，更新于 2026-07-07_

---

## 摘要

本阶段将已稳定的颅骨 implant prediction 协议迁移到 SkullBreak，并完成了
`AdaPoinTr-Implant-SkullBreak seed-0` baseline。任务定义为：

```text
input  = defective skull point cloud
target = implant / defect-region point cloud
output = predicted implant point cloud
final reconstruction = defective skull union predicted implant
```

数据严格按原始 skull 分组。官方训练集包含 114 个 skull、每个 skull 对应
5 种缺损，共 570 个训练 case；官方测试集包含 20 个 skull、共 100 个测试
case。任何同一 skull 的不同 defect 均未跨越训练集、内部验证集或测试集，
官方 train/test complete-skull 内容哈希重叠为 0。

最终模型使用 8192 点 defective skull 作为输入，生成 4096 点 implant；
采用 `learned_only` query、关闭 denoising loss，以 AdamW 训练 100 epochs，
随后仅使用 570 个官方训练 case 重新估计 BatchNorm running statistics，
得到最终权重 `ckpt-last-bncal.pth`。

官方 100-case 测试集上的主要点云结果如下：

| 指标 | AdaPoinTr-Implant | Defective input | 结论 |
| --- | ---: | ---: | --- |
| Final CD-L1 [mm] | 2.2455 | 2.6470 | 改善 0.4014 mm |
| Final CD 改善 case | 82/100 | - | 多数 case 改善 |
| Final ASSD 配对变化 [mm] | -0.3501 | 0 | 95% CI 全部低于 0 |
| Final HD95 配对变化 [mm] | -1.5168 | 0 | 95% CI 全部低于 0 |
| Implant CD-L1 [mm] | 2.8525 | - | 直接缺损区预测 |
| Implant HD95 [mm] | 7.2596 | - | 仍存在局部大偏差 |
| Point-rim CD-L1 [mm] | 5.4586 | - | rim 是主要短板 |

固定 `1.0 mm` surface splat 后的体素结果为：

| 对象 | DSC | ASSD [mm] | HD95 [mm] | Surface Dice@1 mm |
| --- | ---: | ---: | ---: | ---: |
| Predicted implant | 0.2686 | 2.4570 | 7.1255 | 0.3566 |
| Final reconstruction | 0.9470 | 0.2971 | 2.2036 | 0.9074 |
| Defective input | 0.9476 | 0.7402 | 3.7578 | 0.9468 |

结果表明，该 baseline 已经学会为缺失区域提供有效覆盖：final reconstruction
在平均距离、HD95 和体积缺失方面显著优于 defective input；但预测点向健康表面
的近距离贴合、tight-tolerance Surface Dice 和 rim continuity 仍然不足。
这不是实验链路失效，而是当前 AdaPoinTr implant baseline 的主要性能边界，
也是后续 Mamba、边界感知损失与分层高分辨率重建应重点解决的问题。

---

## 范围与边界

### 本报告覆盖

- SkullBreak 原始数据下载、校验、转换与分组
- 114/20 skull 官方 train/test 隔离
- SkullBreakDataset 与 AdaPoinTr runner 接入
- Gate 0：数据完整性检查
- Gate 1：端到端 sanity
- Gate 2：单 case overfit 与 BatchNorm 校准
- Gate 3：small75 失败分析
- Gate 3c：small300 趋势确认
- Gate 4：570-case full seed-0 baseline
- 毫米制 implant、final、input 和 rim 点云指标
- DSC、RVE、Surface Dice、ASSD 和 HD95 体素指标
- 日志、预测、可视化、权重和代码归档
- 已知问题、解决方案、局限与后续建议

### 本报告不覆盖

- ShapeNet34 AdaPoinTr 官方配置 full training
- AdaPoinTr 在 SkullFix 上的 complete-skull reconstruction
- AdaPoinTr-Implant SkullFix seed-0 baseline 的详细过程
- Mamba 模型结构与其后续对照结果

上述内容已有独立报告，本文件只记录 SkullBreak implant baseline。

---

## 任务定义与实验目标

### 为什么直接预测 implant

颅骨修复真正需要生成的是缺损区域，而不是重新生成全部健康颅骨。将网络目标
限定为 implant 有三个直接优势：

1. 保留 defective input 中已经存在的健康解剖结构
2. 将模型容量、损失和评价集中到 defect region
3. 允许 AdaPoinTr 与后续 Mamba 模型使用完全相同的输入、输出和 evaluator

最终重建结果定义为：

```text
final = defective skull union predicted implant
```

评估同时保留三条线：

- predicted implant 对 GT implant
- final reconstruction 对 GT complete skull
- defective input 对 GT complete skull

第三条是不可缺少的零模型基线。由于完整颅骨的大部分区域在输入中已经正确，
仅报告 final whole-skull 指标会掩盖 implant 本身的错误。

### 实验主线

```mermaid
flowchart LR
    accTitle: SkullBreak Implant Baseline Workflow
    accDescr: The grouped experimental workflow from raw SkullBreak volumes through data validation, gated training, official evaluation, voxel analysis, and reproducible archiving.

    raw_data["原始 NRRD 数据"] --> gate_0["Gate 0<br/>转换与分组检查"]
    gate_0 --> gate_1["Gate 1<br/>端到端 sanity"]
    gate_1 --> gate_2["Gate 2<br/>单 case overfit"]
    gate_2 --> gate_3["Gate 3<br/>small75"]
    gate_3 --> diagnose{"是否稳定泛化"}
    diagnose -->|否| gate_3c["Gate 3c<br/>small300"]
    diagnose -->|是| full_train["Gate 4<br/>full seed-0"]
    gate_3c --> full_train
    full_train --> bn_cal["训练集 BN 校准"]
    bn_cal --> point_eval["毫米制 point/rim 评估"]
    point_eval --> voxel_eval["固定协议 voxel 评估"]
    voxel_eval --> archive["归档与 SHA256 校验"]

    classDef process fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#1e3a5f
    classDef decision fill:#fef9c3,stroke:#ca8a04,stroke-width:2px,color:#713f12
    classDef success fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#14532d

    class raw_data,gate_0,gate_1,gate_2,gate_3,gate_3c,full_train,bn_cal,point_eval,voxel_eval process
    class diagnose decision
    class archive success
```

---

## SkullBreak 数据协议

### 数据来源

SkullBreak 包含完整颅骨、五种人工缺损颅骨及对应 implant，原始数据采用 NRRD
体素格式。数据集论文将其定义为自动颅骨 implant 设计与体积形状学习基准。[^1]

本次使用的数据文件及下载校验为：

| 文件 | MD5 |
| --- | --- |
| `skullbreak_training.zip` | `1389265482e37ec2e403ea57649e8afb` |
| `skullbreak_evaluation.zip` | `9681f6771c35faab8288f4b1bf02ee27` |

下载使用 Zenodo record `20308764` 的文件接口。[^2]

### 官方数据规模

| Official split | Skulls | Defects/skull | Cases |
| --- | ---: | ---: | ---: |
| Train | 114 | 5 | 570 |
| Test | 20 | 5 | 100 |
| Total | 134 | 5 | 670 |

五种 defect type 为：

- `bilateral`
- `frontoorbital`
- `parietotemporal`
- `random_1`
- `random_2`

### 防止数据泄漏

SkullBreak 的五个 defect case 共享同一个 complete skull，因此不能按 case 随机
拆分。原子分组单位必须是 `skull_id`。

本实验执行了以下约束：

- 同一 skull 的 5 个 defect 永远位于同一 split
- 官方 20-skull test 不参与训练、BN 校准或 checkpoint 选择
- Gate 3/3c 只在 114 个官方 training skull 内建立 grouped split
- 完整颅骨内容哈希用于检查 official train/test 解剖重复
- 最终检查得到 official train/test complete hash overlap = 0

### 点云转换

原始 NRRD 在本机转换为统一点云：

| 字段 | 含义 | 点数 |
| --- | --- | ---: |
| `partial` | defective skull input | 8192 |
| `gt` | complete skull | 8192 |
| `implant` | GT defect-region target | 4096 |

固定转换 seed 为 `20260703`。每个 case 的 NPZ 同时保存归一化参数与原始体素
几何信息，以便网络输出能够恢复到原始毫米坐标和 NRRD 网格。

转换命令的关键参数为：

```text
n_partial = 8192
n_complete = 8192
n_implant = 4096
gate_split = 0.8,0.1,0.1
monitor_skulls = 10
strict_geometry = true
```

点云 bundle：

```text
skullbreak_pc_8192_4096_seed20260703.tar.gz
SHA256 = 5DD35A2A147E4DE84101EB012822A68F3B138D4375FA59A3857E3E6B4C78A3C1
```

### Gate 0 完整性检查

服务器端 `check_skullbreak_pointcloud.py` 检查结果：

| 检查项 | 结果 |
| --- | ---: |
| Manifest records | 670 |
| Official train skulls | 114 |
| Official train cases | 570 |
| Official test skulls | 20 |
| Official test cases | 100 |
| Gate train cases | 455 |
| Gate val cases | 55 |
| Gate test cases | 60 |
| 每种 defect cases | 134 |
| Implant/missing IoU minimum | 1.000000 |
| Implant/missing IoU mean | 1.000000 |
| Official train/test complete hash overlap | 0 |

坐标范围：

```text
xyz_min = [-0.8710201, -0.9776532, -0.5612881]
xyz_max = [ 0.8500497,  0.9928096,  0.9306410]
```

结论：文件对应关系、五缺损索引、点云 shape、有限数值、归一化、分组隔离和
哈希检查全部通过，Gate 0 通过。

---

## 代码接入

### SkullBreakDataset

新增 `datasets/SkullBreakDataset.py`，其主要行为包括：

- 从 `manifest.jsonl` 读取 case
- 支持 `official_split`、`gate_split` 和 `monitor_split`
- 按 `skull_id` 排序和限制 `max_skulls`
- 支持 `partial`、`gt` 或 `implant` 作为 input
- 支持 `gt` 或 `implant` 作为 target
- 检查输入和目标 shape
- 拒绝 NaN/Inf
- 返回与 PoinTr runner 兼容的 taxonomy、case ID 和 tensor

最终训练协议固定：

```text
input_key  = partial
target_key = implant
```

### Runner 支持

首次运行 Gate 1 时出现：

```text
NotImplementedError: Train phase do not support SkullBreak
```

原因不是数据或模型错误，而是 runner 仅将已有数据集名称列入 point-cloud
训练分支。解决方法是：

- 将 `SkullBreak` 加入 PC-like dataset 集合
- 将 `SkullBreak` 加入不计算 EMD 的医学点云数据集集合
- 保持 Chamfer、F-Score、验证和日志流程与 SkullFix 一致

修复后 forward、backward、validation、checkpoint 和 tqdm 均正常。

### 相关文件

```text
datasets/SkullBreakDataset.py
cfgs/dataset_configs/SkullBreak.yaml
cfgs/SkullBreak_models/AdaPoinTr_implant_sanity.yaml
cfgs/SkullBreak_models/AdaPoinTr_implant_overfit1_bncal.yaml
cfgs/SkullBreak_models/AdaPoinTr_implant_small75_bncal.yaml
cfgs/SkullBreak_models/AdaPoinTr_implant_small300_bncal.yaml
cfgs/SkullBreak_models/AdaPoinTr_implant_full100_bncal.yaml
tools/prepare_skullbreak_pointcloud.py
tools/check_skullbreak_pointcloud.py
tools/test_skullbreak_data_protocol.py
scripts/run_skullbreak_implant_*.sh
scripts/eval_skullbreak_implant.sh
scripts/visualize_skullbreak_implant.sh
```

---

## 模型与训练配置

### AdaPoinTr-Implant 配置

| 项目 | 设置 |
| --- | --- |
| Model | AdaPoinTr |
| Input | defective skull, 8192 points |
| Target/output | implant, 4096 points |
| `num_query` | 256 |
| `num_points` | 4096 |
| Encoder | graph, depth 6, dim 384 |
| Decoder | fc, depth 8, dim 384 |
| Attention heads | 6 |
| KNN `k` | 8 |
| Query selection | `learned_only` |
| Denoise weight | `0.0` |
| Fine coverage weight | `1.0` |
| Fine local weight | `0.0` |

`learned_only` 允许 query 自由移动到输入中不存在的缺损区。若 query 被强制绑定
在 defective skull 的现有表面，生成中心容易偏向健康结构。

### Full seed-0 优化设置

| 项目 | 设置 |
| --- | --- |
| Optimizer | AdamW |
| Initial LR | `1e-4` |
| Weight decay | `5e-4` |
| Total batch size | 8 |
| Epochs | 100 |
| Validation frequency | 10 |
| Workers | 4 |
| Model seed | 0 |
| Deterministic | enabled |
| Checkpoint | epoch 100 `ckpt-last.pth` |
| Deployment checkpoint | `ckpt-last-bncal.pth` |

配置文件：

```text
cfgs/SkullBreak_models/AdaPoinTr_implant_full100_bncal.yaml
```

### BatchNorm 校准

训练完成后：

1. 加载 `ckpt-last.pth`
2. 重置 BatchNorm running mean/variance
3. 不更新任何可学习参数
4. 使用全部 570 个 official training case 前向运行
5. 保存 `ckpt-last-bncal.pth`

BN 校准是固定部署协议的一部分，但不是额外训练。official test 和 monitor 数据
绝不用于更新 BN statistics。

---

## 评价协议

### 毫米制点云指标

所有网络输出先通过样本保存的 centroid 和 scale 反归一化到世界坐标，再计算：

| 指标 | 方向 | 含义 |
| --- | --- | --- |
| CD-L1 [mm] | 越低越好 | 双向平均最近邻距离 |
| ASSD [mm] | 越低越好 | 对称平均表面距离 |
| HD95 [mm] | 越低越好 | 双向距离的稳健高分位误差 |
| Pred-to-Ref [mm] | 越低越好 | 预测点偏离参考表面的程度 |
| Ref-to-Pred [mm] | 越低越好 | GT 表面未被预测覆盖的程度 |
| NSD@0.5/1/2 mm | 越高越好 | 给定物理容差内的表面一致性 |

当前 point evaluator 中 CD-L1 与 ASSD 的基础定义均来自双向最近邻距离，但
final union 的采样/去重路径可能使其配对统计不完全相同，因此报告保留二者。

### Rim 指标

以 defective skull 上距离 GT implant 小于固定 rim band 的点作为参考边界，
比较 predicted implant 在接触带附近的覆盖：

- rim contact CD-L1
- rim contact HD95
- rim contact NSD@0.5/1/2 mm
- GT-rim-to-pred mean
- GT-rim-to-pred p95

### 体素指标

点云输出映射回原始 NRRD 网格后采用固定 surface splat：

```text
splat_radius_mm = 1.0
rim_band_mm = 2.0
tolerances_mm = 0.5, 1.0, 2.0
```

计算：

- DSC
- Relative Volume Error, RVE
- Absolute RVE
- Surface ASSD
- Surface HD95
- Surface Dice@0.5/1/2 mm
- 体素协议下的 rim 指标

> **重要限制：** 这里的 DSC 是 4096 点 implant 经 `1.0 mm` surface splat
> 后得到的 voxelized-prediction DSC。只有当所有对照模型采用完全相同的点云
> 到体素转换协议时，DSC 才能公平比较。

### 统计协议

结果保存：

- per-case CSV
- 100-case descriptive statistics
- 20-skull macro statistics
- 五种 defect type 分层统计
- 2000 次 bootstrap 均值 95% CI
- final 与 defective input 的 paired delta
- improved case count 和 improvement rate

由于每个 skull 对应 5 个相关 case，论文主结论不能将 100 个 case 当成 100 个
独立受试者。正式推断应优先引用 20-skull macro 或 skull-cluster bootstrap；
case-level 结果主要用于误差分布和 defect-type 分析。

---

## Gate 1：端到端 sanity

### 设置

Gate 1 从 grouped train、val、test 各取 1 个 skull，即每个 split 包含完整的
5 种 defect。训练 1 epoch，batch size 2。

### 首次故障与修复

首次运行在第一批训练前被 runner 拒绝：

```text
NotImplementedError: Train phase do not support SkullBreak
```

修复 runner 的 dataset dispatch 后重新运行成功。

### 结果

epoch 1 validation：

```text
F-Score = 0.0008
CDL1    = 628.0365
CDL2    = 1252.1581
EMD     = 0.0000
```

并成功保存：

```text
ckpt-last.pth
ckpt-epoch-001.pth
```

这些是归一化空间中的随机初始化短训练结果，不用于医学性能判断。Gate 1 的
结论仅是：数据加载、模型 forward/backward、optimizer、validation、tqdm、
日志与 checkpoint 全链路通过。

---

## Gate 2：单 case overfit

### 设置

| 项目 | 设置 |
| --- | --- |
| Unique case | 1 |
| Case | `train__000__bilateral` |
| Repeat | 8 |
| Epochs | 300 |
| Batch size | 8 |
| Query | `learned_only` |
| Denoising | disabled |
| Post-process | training-only BN calibration |

### 毫米制结果

| 对象 | CD [mm] | HD95 [mm] | NSD@1 mm |
| --- | ---: | ---: | ---: |
| Predicted implant | 1.4997 | 3.4713 | 0.3246 |
| Final reconstruction | 1.9478 | 3.7736 | 0.1931 |
| Defective input | 2.4991 | 4.7159 | 0.2045 |

Rim：

| 指标 | 结果 |
| --- | ---: |
| Rim CD [mm] | 0.8879 |
| Rim HD95 [mm] | 5.1148 |
| Rim NSD@1 mm | 0.7398 |
| GT-rim-to-pred p95 [mm] | 3.7092 |

### 结论

- implant CD 小于 2 mm
- implant HD95 小于 5 mm
- implant NSD@1 大于 0.30
- final CD 和 HD95 均优于 defective input
- 可视化显示 implant 的位置、朝向和覆盖范围合理

Gate 2 通过，说明模型和损失能够学习 defective-to-implant 映射。

---

## Gate 3：small75 失败及诊断

### 设置

| Split | Skulls | Cases |
| --- | ---: | ---: |
| Train | 8 | 40 |
| Validation | 2 | 10 |
| Internal test | 2 | 10 |

训练 75 epochs，batch size 4，随后执行 BN calibration。

### 结果

| 对象 | CD [mm] | HD95 [mm] | NSD@1 mm |
| --- | ---: | ---: | ---: |
| Predicted implant | 25.7862 | 45.5416 | 0.0292 |
| Final reconstruction | 2.7644 | 7.9425 | 0.1728 |
| Defective input | 2.5026 | 5.9156 | 0.2068 |

Rim：

```text
CD             = 34.3518 mm
HD95           = 69.0731 mm
NSD@1          = 0.1109
GT-rim p95 gap = 43.4344 mm
```

### Per-case 现象

预测并非全部 NaN、空点云或统一原点坍缩，但不同 skull 间泛化严重不稳定。
部分 case 尚可，部分 case 产生大范围错位。尤其 `train:021` 的某些缺损：

- `random_2` implant CD 约 38.95 mm
- `parietotemporal` implant CD 约 59.41 mm
- `bilateral` implant CD 约 87.65 mm

可视化中预测点云呈弯曲片状或通用 implant 形态，但未正确落在对应 defect
位置，说明模型学到的是小样本上的形状先验，而不是稳定的解剖条件映射。

### 诊断结论

Gate 3 失败，但失败类型不是工程链路故障：

- 数据和坐标恢复正常
- BN calibration 已执行
- 模型输出为有限数值
- 失败集中在跨 skull 泛化
- 8 个训练 skull 无法覆盖 SkullBreak 的解剖和缺损变化

因此没有直接启动 full baseline，而是增加 Gate 3c。

---

## Gate 3c：small300 趋势确认

### 设置

| Split | Skulls | Cases |
| --- | ---: | ---: |
| Train | 60 | 300 |
| Validation | 6 | 30 |
| Internal test | 6 | 30 |

训练 100 epochs，batch size 8，执行 training-only BN calibration，并导出
30 个 internal-test prediction。

### 配对结果

Final reconstruction 相对 defective input：

| 指标 | 改善 cases | Mean delta | 95% bootstrap CI |
| --- | ---: | ---: | ---: |
| CD-L1 [mm] | 25/30 | -0.2640 | [-0.4565, -0.0511] |
| ASSD [mm] | 22/30 | -0.1971 | [-0.4038, 0.0347] |
| HD95 [mm] | 17/30 | -0.3860 | [-1.7890, 1.1360] |
| Ref-to-Pred [mm] | 30/30 | -1.1322 | [-1.3940, -0.8764] |
| Pred-to-Ref [mm] | 0/30 | +0.6042 | [0.4142, 0.8614] |
| NSD@1 mm | 0/30 | -0.0279 | [-0.0292, -0.0266] |

### 解释

small300 显示了清晰但不完美的趋势：

- final CD 在 83.3% case 上改善，且均值 CI 不跨 0
- GT complete 到 final 的覆盖距离在全部 case 上改善
- 预测 implant 补上了缺失区域
- 新生成点与精确健康表面的局部贴合不足
- tight-tolerance NSD 全面下降

Gate 3c 的目的不是达到最终性能，而是确认数据量增加后模型不再系统性错位，
且 full training 具有合理收益方向。该 Gate 通过，支持进入 Gate 4。

---

## Gate 4：Full seed-0 baseline

### 数据使用

| 用途 | Skulls | Cases | 是否参与参数/BN |
| --- | ---: | ---: | --- |
| Official train | 114 | 570 | 是 |
| Train monitor | 10 | 50 | 仅观察，属于 train |
| Official test | 20 | 100 | 否 |

最终评估只使用 `full100_bncal_official_test`。monitor 与训练数据重叠，不作为
论文测试结果。

### Checkpoint

```text
experiments/AdaPoinTr_implant_full100_bncal/
  SkullBreak_models/skullbreak_implant_full100_bncal/
    ckpt-last.pth
    ckpt-last-bncal.pth
    ckpt-last-bncal.pth.json
```

checkpoint metadata：

```text
epoch       = 100
F-Score     = 0.2111963
CDL1        = 18.2232295
CDL2        = 0.9367437
EMDistance  = 0.0
```

这些是 runner 的归一化空间指标，只用于追踪训练状态。正式医学结果使用下面的
毫米制和体素指标。

---

## Full baseline 点云结果

### Overall case-level 均值

由于五种 defect 各有 20 个 case，下表的 defect-equal mean 与 100-case mean
一致：

| 对象/指标 | 结果 |
| --- | ---: |
| Implant CD-L1 [mm] | 2.8525 |
| Implant HD95 [mm] | 7.2596 |
| Final CD-L1 [mm] | 2.2455 |
| Defective input CD-L1 [mm] | 2.6470 |
| Point-rim CD-L1 [mm] | 5.4586 |

### Final 与 input 的配对比较

| 指标 | 改善 cases | Mean delta | 95% bootstrap CI | 解释 |
| --- | ---: | ---: | ---: | --- |
| CD-L1 [mm] | 82/100 | -0.4014 | [-0.4987, -0.3101] | 明确改善 |
| ASSD [mm] | 75/100 | -0.3501 | [-0.4418, -0.2584] | 明确改善 |
| HD95 [mm] | 56/100 | -1.5168 | [-2.2582, -0.8430] | 均值改善 |
| Ref-to-Pred | 100/100 | 下降 | - | 缺失覆盖改善 |
| Pred-to-Ref | 0/100 | 上升 | - | 新点局部贴合变差 |
| NSD@0.5/1/2 mm | 几乎全部变差 | 下降 | - | tight tolerance 短板 |

这里出现的“平均距离改善但 NSD 下降”并不矛盾。defective input 的已有健康点
天然位于 GT 表面附近，因此 Pred-to-Ref 和 NSD 很高；加入 predicted implant
后，GT 缺失区域得到覆盖，Ref-to-Pred 大幅改善，但新增点存在毫米级偏差，
从而拉低 tight-tolerance NSD。

### 按 defect type 分层

| Defect | Implant CD [mm] | Implant HD95 [mm] | Final CD [mm] | Input CD [mm] | Rim CD [mm] |
| --- | ---: | ---: | ---: | ---: | ---: |
| Bilateral | 3.0980 | 7.7821 | 2.2685 | 2.8849 | 5.5313 |
| Frontoorbital | 2.6049 | 7.0499 | 2.2397 | 2.2053 | 4.6225 |
| Parietotemporal | 2.6795 | 6.5502 | 2.2402 | 2.5178 | 4.4809 |
| Random 1 | 3.1481 | 8.2975 | 2.2679 | 2.7299 | 6.2840 |
| Random 2 | 2.7320 | 6.6181 | 2.2111 | 2.8970 | 6.3742 |

### Defect-type 分析

- **Bilateral：** final CD 改善明显，但 implant 与 rim 难度较高
- **Frontoorbital：** implant CD 最低，但 final CD 从 2.2053 增至 2.2397 mm，
  是唯一均值略退化的 defect type
- **Parietotemporal：** implant HD95 最低，整体较稳定
- **Random 1：** implant CD 和 HD95 均为五类中最高，随机缺损变化更难建模
- **Random 2：** final CD 改善最大，但 rim CD 最高，说明总体覆盖与边界贴合
  可以同时呈现相反趋势

---

## Full baseline 体素结果

### Implant 指标

| 指标 | Mean |
| --- | ---: |
| DSC | 0.2686 |
| RVE | -0.4572 |
| Absolute RVE | 0.4959 |
| Surface ASSD [mm] | 2.4570 |
| Surface HD95 [mm] | 7.1255 |
| Surface Dice@1 mm | 0.3566 |

RVE 为负说明 splat 后的 predicted implant 体积平均偏小。约 49.6% 的 absolute
RVE 表明点数固定并不等价于体积正确：点分布密度、表面覆盖和 splat 重叠都会
影响 voxel volume。

### Final reconstruction 与 defective input

| 指标 | Final | Input | Final - Input |
| --- | ---: | ---: | ---: |
| DSC | 0.9470 | 0.9476 | -0.0005 |
| RVE | -0.0606 | -0.0981 | +0.0374 |
| Absolute RVE | 0.0611 | 0.0981 | -0.0370 |
| Surface ASSD [mm] | 0.2971 | 0.7402 | -0.4431 |
| Surface HD95 [mm] | 2.2036 | 3.7578 | -1.5542 |
| Surface Dice@1 mm | 0.9074 | 0.9468 | -0.0394 |

### Paired voxel comparison

| 指标 | 改善 cases | Mean delta | 95% bootstrap CI |
| --- | ---: | ---: | ---: |
| DSC | 41/100 | -0.0005 | [-0.0017, 0.0005] |
| Absolute RVE | 100/100 | -0.0370 | [-0.0384, -0.0355] |
| Surface ASSD [mm] | 86/100 | -0.4431 | [-0.5423, -0.3558] |
| Surface HD95 [mm] | 40/100 | -1.5542 | [-2.6057, -0.5982] |
| Surface Dice@1 mm | 0/100 | -0.0394 | [-0.0420, -0.0369] |

### Voxel rim

| 指标 | Mean |
| --- | ---: |
| Rim contact CD-L1 [mm] | 2.9853 |
| Rim contact HD95 [mm] | 15.4752 |
| Rim contact NSD@1 mm | 0.5933 |

point-rim 与 voxel-rim 的数值不可直接互换。前者基于点云接触带，后者经过 NRRD
网格映射、surface splat 和体素表面提取。两者都表明边界平均接触并非完全失败，
但长尾误差较大。

### 体素结果解释

1. **Final DSC 基本持平。** 完整颅骨的大体积健康区域主导 DSC，缺损区改善被
   稀释；CI 跨 0，不能声称 final DSC 明确优于 input。
2. **体积缺失明确改善。** RVE 从约 -9.81% 改善到 -6.06%，absolute RVE 在
   100/100 case 上改善。
3. **平均表面距离明确改善。** ASSD 降低约 0.443 mm。
4. **HD95 均值改善但 case count 不占多数。** 40/100 case 改善却产生显著
   负均值，说明少数原本很差的 case 获得了较大改善。
5. **Surface Dice@1 mm 全面下降。** 预测 implant 提供覆盖，但其表面未稳定
   落入严格 1 mm 容差。

---

## 可视化分析

Full baseline 为官方 test 保存了 15 组可视化，每组包括：

```text
input_defective
prediction_implant
ground_truth_implant
final_reconstruction
ground_truth_complete
```

整体观察：

- 模型能够把 implant 放在缺损的大致空间位置
- 输出不再出现 small75 中大范围统一错位
- implant 主体形状和方向通常合理
- 边缘存在稀疏、飞点、过度平滑和覆盖不足
- 某些复杂 defect 的 implant 边界不能与 defect rim 闭合
- frontoorbital 和 random defect 的局部误差更值得重点检查

因此可视化与定量指标一致：模型已经解决“缺损区域在哪里、需要补什么大致
形状”，但尚未充分解决“边界如何精确贴合、表面如何达到 1 mm 级一致性”。

---

## 主要问题与解决方案

### 问题 1：官方数据下载入口不稳定

**现象：** 旧的 training/evaluation 直链失效或重定向异常。

**处理：**

- 检索官方页面、数据论文和可用归档
- 从 Zenodo record 下载两个 zip
- 使用 MD5 验证下载完整性
- 保留原始压缩包校验值和本地 raw 目录

### 问题 2：本机 NRRD 转点云耗时很长

**现象：** 134 个 skull、670 个 case 的 NRRD 读取、表面提取、采样和校验在
Windows 本机运行数小时。

**原因：**

- 原始体积尺寸大
- 每个 skull 对应五种 defect
- 同时生成 partial、complete、implant
- 严格几何检查和 checksum 增加 I/O

**处理：**

- 保留已完成的 deterministic point-cloud bundle
- 使用 SHA256 防止无意义重复转换
- 服务器只上传数百 MB 点云包，不上传全部 NRRD
- 后续实验复用 NPZ 和 manifest

### 问题 3：Runner 不识别 SkullBreak

**现象：**

```text
Train phase do not support SkullBreak
```

**处理：**

- 将 SkullBreak 注册为 PC-like dataset
- 复用 SkullFix 的 tensor 数据路径
- 对医学点云关闭未实现的 EMD
- 重新运行 Gate 1 验证所有训练环节

### 问题 4：Optional GRNet import 警告

**现象：**

```text
[models] skip optional import models.GRNet: No module named 'gridding'
```

**判断：** 当前运行模型是 AdaPoinTr，不依赖 GRNet 的 `gridding` 扩展。该日志
是可选模型导入提示，不影响 AdaPoinTr forward、loss、checkpoint 或评估。

### 问题 5：Gate 3 small75 严重泛化失败

**现象：** implant CD 达 25.7862 mm，若干 case 达 40-88 mm。

**处理：**

- 检查 per-case CSV，确认错误集中在特定 skull/defect
- 检查可视化，排除坐标反归一化和空输出
- 不把 small75 当作 full baseline 趋势
- 增加 small300，以 60 个 skull、300 cases 重新验证

**结果：** small300 的 final CD 在 25/30 case 改善，支持进入 full training。

### 问题 6：平均距离改善但 NSD/Surface Dice 下降

**现象：**

- CD、ASSD、HD95 和 Ref-to-Pred 改善
- Pred-to-Ref、NSD 和 Surface Dice@1 mm 变差

**解释：**

- defective input 已有表面天然接近 GT
- predicted implant 增加了对缺失区的覆盖
- 新增点并未精确贴合 GT surface
- 覆盖改善与局部表面精度是两个不同目标

**结论：** 不能只看 whole-skull CD，也不能只看 input-dominated NSD；必须联合
报告 implant、final、input、方向距离和 rim。

### 问题 7：Checkpoint 导致存储压力

**现象：** 多轮 Gate 和 epoch checkpoint 累积占用服务器空间。

**处理：**

- 训练前检查至少 8 GiB 可用空间
- full run 只长期保留 `ckpt-last.pth` 和 `ckpt-last-bncal.pth`
- 不保存大量中间 epoch checkpoint
- 训练结束后导出 prediction 和关键日志
- 归档在本机验证 SHA256 后删除服务器 archive 副本

---

## 结果的正确结论

### 可以得出的结论

- 数据转换、分组、训练、BN 校准、评估和归档协议可复现
- 官方 train/test 不存在 skull-level 泄漏
- AdaPoinTr 能学习 SkullBreak defective-to-implant 映射
- final reconstruction 的平均距离和覆盖明显优于 defective input
- 体积缺失和平均表面距离获得稳定改善
- random defect、bilateral 和 rim fitting 是当前难点
- baseline 足以作为后续 Mamba 模型的固定 seed-0 对照

### 不能过度声称的结论

- 不能用 final whole-skull DSC 证明 implant 本身高度准确
- 不能忽略 Surface Dice@1 mm 和 NSD 的下降
- 不能将 100 case 当作 100 个独立 skull
- 不能将 surface-splat DSC 与原生 voxel segmentation DSC 直接比较
- 不能把 BN calibration 使用 official test 数据
- 不能把 monitor 结果当作独立测试结果

---

## 对后续 Mamba 对照实验的要求

为了保证公平比较，后续模型必须固定：

| 项目 | 固定协议 |
| --- | --- |
| Dataset bundle | 同一 SkullBreakPC |
| Train/test | 114/20 skull official split |
| Model seed | 0，后续再增加多 seed |
| Input points | 8192 |
| Output implant points | 4096 |
| Normalization | 同一 case metadata |
| Point evaluator | 同一毫米制实现 |
| Voxel splat | radius 1.0 mm |
| Rim band | 2.0 mm |
| Test cases | 同一 100 cases |
| Statistics | case、skull macro、defect type、paired |

优先改进目标：

1. 降低 implant Ref-to-Pred，保持缺损覆盖
2. 同时降低 Pred-to-Ref，减少漂移点
3. 提升 NSD/Surface Dice@1 mm
4. 降低 rim HD95 和 GT-rim p95 gap
5. 改善 frontoorbital、bilateral 和 random defect 的稳定性

建议的模型方向：

- defect-aware 或 cross-boundary token 建模
- Mamba 长程状态空间编码
- rim-aware local feature aggregation
- coarse-to-fine implant generation
- boundary-weighted Chamfer/Surface Dice surrogate
- coverage 与 precision 分离的双向损失
- 高分辨率迭代细化

---

## 产物与归档

### 服务器主要产物

```text
cfgs/SkullBreak_models/AdaPoinTr_implant_full100_bncal.yaml

experiments/AdaPoinTr_implant_full100_bncal/
  SkullBreak_models/skullbreak_implant_full100_bncal/
    config.yaml
    ckpt-last.pth
    ckpt-last-bncal.pth
    ckpt-last-bncal.pth.json

logs/skullbreak_implant/
logs/skullbreak_implant_eval/full100_bncal_monitor/
logs/skullbreak_implant_eval/full100_bncal_official_test/
logs/skullbreak_implant_eval/full100_predictions_test/

experiments/visualizations/skullbreak_implant_full100_bncal_test/
```

### Baseline archive

```text
skullbreak_adapointr_implant_seed0_v1.tar
size   = 420 MB
SHA256 = 3533f697cf6604b2ba1ada6d2801fa3ca76eb4eda013334a623a678ef0976b68
```

服务器和 Windows 本机的 SHA256 比较结果：

```text
True
```

归档包含：

- config 和 resolved config
- `ckpt-last-bncal.pth` 及 JSON metadata
- 训练日志
- official-test summary JSON
- official-test per-sample CSV
- 100 个 prediction NPZ 和 manifest
- 15 组可视化
- 相关代码、脚本与文档
- pip/conda/system 环境信息
- Git 状态和代码 snapshot
- 内部逐文件 `MANIFEST.sha256`

### 本机固定目录

```text
D:\ResearchBackups\AdaPoinTr\SkullBreak_implant_seed0_v1\
├── skullbreak_adapointr_implant_seed0_v1.tar
├── skullbreak_adapointr_implant_seed0_v1.tar.sha256
└── voxel_evaluation\
    ├── skullbreak_voxel_per_sample.csv
    └── skullbreak_voxel_summary.json
```

原始 SkullBreak NRRD 和转换后的 SkullBreakPC 不放入 baseline model archive，
但其下载校验、点云 bundle SHA256 和转换 seed 已记录。

---

## 复现入口

### 数据检查

```bash
python tools/check_skullbreak_pointcloud.py \
  --data_root ~/datasets/SkullBreakPC \
  --expected_train_skulls 114 \
  --expected_test_skulls 20 \
  --verify_checksums
```

### Full training

```bash
tmux new -s skullbreak_full_seed0
bash scripts/run_skullbreak_implant_full100_bncal.sh
```

### 断点续训

```bash
tmux new -s skullbreak_full_seed0_resume
RESUME=1 bash scripts/run_skullbreak_implant_full100_bncal.sh
```

### 归档验证

```bash
tar -xf skullbreak_adapointr_implant_seed0_v1.tar -C <restore_dir>
bash <restore_dir>/scripts/verify_skullbreak_implant_seed0_archive.sh \
  <restore_dir>
```

验证器要求：

- 所有内部 SHA256 通过
- official summary 和 per-sample CSV 存在
- prediction NPZ 数量为 100
- visualization 目录数量至少为 15
- config、checkpoint、metadata 和 code snapshot 存在

---

## 最终结论

本阶段已经完成了 SkullBreak AdaPoinTr implant baseline 从原始数据到可恢复归档
的完整闭环。核心成果不是单一指标，而是建立了一个具备以下属性的固定对照：

- 无 skull-level 数据泄漏
- 输入、目标和输出定义明确
- 所有距离在原始毫米坐标中计算
- 同时报告 implant、final、input 和 rim
- 同时保留点云与固定协议体素指标
- 有 per-case、skull macro 和 defect-type 统计
- 有 deterministic seed、BN 校准、日志、预测和可视化
- 有本机离线 archive 与 SHA256 校验

最终模型能够显著改善缺损覆盖、平均表面距离、HD95 和体积缺失，但在
1 mm 级局部表面一致性、predicted-point precision 和 rim continuity 上仍有
清晰短板。这个性能轮廓足够稳定，也足够“有问题可改”，适合作为后续
Mamba-based cranial implant reconstruction 的 seed-0 公平基线。

下一阶段应先提交当前代码并创建 annotated Git tag
`skullbreak-adapointr-implant-seed0-v1`，随后在完全冻结的数据划分和 evaluator
下开展 Mamba 模型实验。

---

## 参考资料

[^1]: Kodym, O., Li, J., Pepe, A., et al. (2021). "SkullBreak / SkullFix - Dataset for automatic cranial implant design and a benchmark for volumetric shape learning tasks." _Data in Brief_. https://www.sciencedirect.com/science/article/pii/S2352340921001864

[^2]: Zenodo. (2026). "SkullBreak dataset files, record 20308764." https://zenodo.org/records/20308764

