# SkullBreak AdaPoinTr-Implant Seed-0 Baseline 协议

_适用于将已冻结的 SkullFix implant 协议迁移到 SkullBreak；最后更新：2026-07-03_

---

## 目标与结论

本方案是合理的，但必须把原计划补充为五个 Gate，并将“按 skull 分组”贯彻到转换、划分、统计和最终归档：

```text
input  = defective skull point cloud
target = implant / defect-region point cloud
output = predicted implant point cloud
final  = defective skull union predicted implant
```

SkullBreak 官方设置包含 114 个训练 skull 和 20 个测试 skull，每个 skull 有 5 种缺损，因此分别形成 570 和 100 个 case。五类缺损为 `bilateral`、`frontoorbital`、`parietotemporal`、`random_1` 和 `random_2`。[^1]

```mermaid
flowchart LR
    accTitle: SkullBreak Baseline Gates
    accDescr: SkullBreak implant baseline workflow from grouped data validation through sanity, single-case memorization, subset validation, and fixed seed-0 full evaluation

    gate_0["Gate 0<br/>转换与分组检查"] --> gate_1["Gate 1<br/>Sanity"]
    gate_1 --> gate_2["Gate 2<br/>单 case overfit"]
    gate_2 --> gate_3["Gate 3<br/>小规模分组实验"]
    gate_3 --> gate_4["Gate 4<br/>Seed-0 full baseline"]
    gate_4 --> archive["归档代码、权重与结果"]

    classDef check fill:#fef9c3,stroke:#ca8a04,stroke-width:2px,color:#713f12
    classDef process fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#1e3a5f
    classDef success fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#14532d

    class gate_0 check
    class gate_1,gate_2,gate_3,gate_4 process
    class archive success
```

关键约束如下：

- 同一完整 skull 的 5 个 defect 必须始终位于同一 split
- 官方 20-skull test 不参与调参、BN 重估或 checkpoint 选择
- Gate 3 只使用官方 training skull 内部的 group split
- Gate 4 使用全部 114 个官方 training skull
- Gate 4 的 10-skull `monitor` 子集仍属于训练数据，只用于观察曲线
- 最终模型固定为第 100 epoch 的 `ckpt-last-bncal.pth`
- 最终报告同时给出 case-level、skull-macro 和 defect-type 分层统计

> **重要：** 如果只有公开的 114-skull training 包，可以完成 Gate 0–3 和训练集内部开发实验，但不能把内部 test split 称为官方 SkullBreak test。官方 20-skull/100-case 结果要求独立 evaluation 数据及对应 GT。

只有 training 包时，转换命令省略 `--evaluation_root`，并显式增加：

```powershell
--expected_test_skulls 0
```

此时 Gate 1–3 使用 `gate_split`；不要运行 Gate 4 的 official-test 步骤。

## 数据结构

论文和公开实现采用下列目录结构。[^2]

- 官方数据页：`https://autoimplant2021.grand-challenge.org/Dataset/`
- 官方联系邮箱：`autoimplant.challenge@gmail.com`
- 论文原 training/evaluation 直链截至 2026-07-03 已重定向后返回
  HTTP 404，不能继续作为有效下载入口
- 挑战已关闭，但官方数据页明确说明数据仍可按请求获取

```text
SkullBreak/
├── training/
│   ├── complete_skull/
│   ├── defective_skull/
│   │   ├── bilateral/
│   │   ├── frontoorbital/
│   │   ├── parietotemporal/
│   │   ├── random_1/
│   │   └── random_2/
│   └── implant/
│       └── <相同的五类目录>
└── evaluation/
    └── <与 training 相同的三级结构>
```

每个 `complete_skull/<id>.nrrd` 必须在五个 `defective_skull/<type>/` 和五个 `implant/<type>/` 目录中各有同名文件。

原始 NRRD 体积较大，不建议上传到 50 GB 服务器。推荐在本机完成转换，只上传数百 MB 量级的点云包。

## Gate 0：转换与完整性检查

### 本机转换

在 PowerShell 中执行：

```powershell
Set-Location "C:\Users\zhj\Documents\Codex\2026-06-06\mamba-ccf-c-1-high-resolution\work\PoinTr"

python tools\prepare_skullbreak_pointcloud.py `
  --training_root "D:\dataset\SkullBreak\training" `
  --evaluation_root "D:\dataset\SkullBreak\evaluation" `
  --output_root "D:\dataset\SkullBreakPC" `
  --n_partial 8192 `
  --n_complete 8192 `
  --n_implant 4096 `
  --seed 20260703 `
  --gate_split 0.8,0.1,0.1 `
  --monitor_skulls 10 `
  --strict_geometry
```

`--strict_geometry` 只约束 shape、space directions 和 origin 一致。SkullBreak 使用了不规则缺损及边缘处理，`implant` 与 `complete - defective` 的逐体素 IoU 是质量诊断项，不默认作为失败条件。只有确认本地数据版本应满足给定阈值时，才增加 `--strict_quality`。

### 本机检查

```powershell
python tools\check_skullbreak_pointcloud.py `
  --data_root "D:\dataset\SkullBreakPC" `
  --expected_train_skulls 114 `
  --expected_test_skulls 20 `
  --verify_checksums
```

Gate 0 通过标准：

| 检查项 | 期望结果 |
| --- | ---: |
| Official train skulls | 114 |
| Official train cases | 570 |
| Official test skulls | 20 |
| Official test cases | 100 |
| 每个 skull 的 defect 数 | 5 |
| Official train/test 完整颅骨 hash 重叠 | 0 |
| Gate split 中 skull 跨集合 | 0 |
| NPZ shape、dtype、有限值、SHA256 | 全部通过 |

### 打包并上传

```powershell
tar -czf "D:\skullbreak_pc_8192_4096_seed20260703.tar.gz" `
  -C "D:\dataset\SkullBreakPC" .
```

服务器执行：

```bash
mkdir -p ~/datasets/SkullBreakPC
tar -xzf ~/skullbreak_pc_8192_4096_seed20260703.tar.gz \
  -C ~/datasets/SkullBreakPC

cd ~/adapointr_work/PoinTr
mkdir -p data
ln -s ~/datasets/SkullBreakPC data/SkullBreakPC

python tools/check_skullbreak_pointcloud.py \
  --data_root ~/datasets/SkullBreakPC \
  --expected_train_skulls 114 \
  --expected_test_skulls 20 \
  --verify_checksums
```

如果 `data/SkullBreakPC` 已存在，先用 `ls -ld data/SkullBreakPC` 检查目标，不要覆盖未知目录。

## Gate 1：Sanity

Gate 1 从 group-level train/val/test 各取 1 个 skull，每个 skull 包含完整的 5 种 defect。

```bash
cd ~/adapointr_work/PoinTr
chmod +x scripts/*skullbreak*.sh
tmux new -s skullbreak_gate1
bash scripts/run_skullbreak_implant_sanity.sh
```

按 `Ctrl+b`，松开后按 `d`，可脱离会话。重新进入：

```bash
tmux attach -t skullbreak_gate1
```

通过标准：

- 日志显示 `input_key=partial target_key=implant`
- train、val、test 分别加载 1 个 skull、5 个 case
- 前向、反向和 validation 无 NaN、OOM 或路径错误
- 生成 `ckpt-last.pth` 和训练日志

## Gate 2：单 case overfit

Gate 2 使用同一个 training case 训练和验证，并在训练后重估 BatchNorm running statistics。

```bash
tmux new -s skullbreak_gate2
bash scripts/run_skullbreak_implant_overfit1_bncal.sh
```

结果目录：

```text
logs/skullbreak_implant_eval/overfit1_bncal/
experiments/visualizations/skullbreak_implant_overfit1_bncal/
experiments/AdaPoinTr_implant_overfit1_bncal/SkullBreak_models/
```

建议的暂定通过标准：

- 300 epoch 训练 loss 持续下降且有限
- BN calibration 后的 implant `CD-L1 <= 2 mm`
- implant `HD95 <= 5 mm`
- implant `NSD@1mm >= 0.30`
- 预测 implant 的位置、朝向和覆盖范围与 GT 一致

阈值是工程 Gate，不是论文最终指标。若某个困难 case 略超阈值，应结合训练曲线与可视化判断；若预测完全错位，则不能进入 Gate 3。

## Gate 3：小规模分组实验

Gate 3 使用官方 training skull 内部的 group split：

| 子集 | Skulls | Cases |
| --- | ---: | ---: |
| Train | 8 | 40 |
| Validation | 2 | 10 |
| Internal test | 2 | 10 |

```bash
tmux new -s skullbreak_gate3
bash scripts/run_skullbreak_implant_small75_bncal.sh
```

通过标准：

- 所有 split 均以完整 skull 为单位
- 75 epoch、BN calibration、val/test evaluator 和可视化全部结束
- `summary.json` 包含 `statistics_case_level`、`statistics_skull_macro` 和 `by_defect_type`
- internal test 指标明显优于未训练输出
- per-case 结果不存在统一塌缩、整体平移或单一 defect 类系统性失败

Gate 3 只是管线与泛化趋势检查，不能作为官方测试结果。

## Gate 4：Full seed-0 baseline

Gate 4 固定使用：

| 项目 | 设置 |
| --- | --- |
| Training | 114 skulls / 570 cases |
| Monitor | 10 training skulls / 50 cases |
| Official test | 20 skulls / 100 cases |
| Epochs | 100 |
| Total batch size | 8 |
| Seed | 0 |
| Deterministic mode | 开启 |
| Query selection | `learned_only` |
| Denoise weight | `0.0` |
| Output points | 4096 implant points |
| Final checkpoint | `ckpt-last-bncal.pth` |

脚本在 `$HOME` 可用空间低于 8 GiB 时拒绝启动。建议实际开始前至少保留 12 GiB。

```bash
df -h ~
tmux new -s skullbreak_full_seed0
bash scripts/run_skullbreak_implant_full100_bncal.sh
```

断点续训：

```bash
tmux new -s skullbreak_full_seed0_resume
RESUME=1 bash scripts/run_skullbreak_implant_full100_bncal.sh
```

脚本结束后应存在：

```text
experiments/AdaPoinTr_implant_full100_bncal/
  SkullBreak_models/skullbreak_implant_full100_bncal/
    ckpt-last.pth
    ckpt-last-bncal.pth
    ckpt-last-bncal.pth.json

logs/skullbreak_implant/
logs/skullbreak_implant_eval/full100_bncal_monitor/
logs/skullbreak_implant_eval/full100_bncal_official_test/
logs/skullbreak_implant_eval/full100_predictions_test/
experiments/visualizations/skullbreak_implant_full100_bncal_test/
```

`monitor` 与 training 重叠，因此其数值只能用于诊断训练稳定性。论文表格使用 `full100_bncal_official_test`。

## 最终评价协议

点云主指标全部在原始物理坐标中计算：

- implant CD-L1 / ASSD `[mm]`
- implant HD95 `[mm]`
- implant NSD@0.5/1/2 mm
- implant `Pred->Ref` 与 `Ref->Pred` 均值
- rim contact CD、HD95、NSD 和 GT-rim-to-pred gap
- final reconstruction 对 complete skull 的相同指标
- defective input 对 complete skull 的配对基线

SkullBreak 有 5 个相关 case 共享同一 skull，因此报告层级必须包括：

1. 100-case micro/均值统计
2. 20-skull macro 统计与以 skull 为抽样单位的置信区间
3. 五种 defect type 各自的 20-case 分层统计
4. final reconstruction 相对 defective input 的配对变化

点云预测导出后，在保存原始 NRRD 的本机计算体素指标：

```powershell
python tools\evaluate_skullfix_voxel_metrics.py `
  --prediction_manifest "D:\...\full100_predictions_test\predictions_manifest.jsonl" `
  --raw_root "D:\dataset\SkullBreak" `
  --out_dir "D:\...\full100_voxel_test" `
  --dataset_label SkullBreak `
  --output_prefix skullbreak `
  --splat_radius_mm 1.0 `
  --rim_band_mm 2.0
```

体素结果包括 implant/final 的 DSC、Surface Dice、ASSD、HD95、RVE 和 rim 指标。点云转体素的 DSC 依赖固定 splat radius，必须连同 `1.0 mm` 参数一起报告；它不能与原生体素模型在不同后处理协议下的 DSC 直接比较。

## 风险与停止条件

### 数据泄漏

如果按 case 随机划分，来自同一完整 skull 的不同 defect 会跨 train/test，结果将被严重高估。任何 split 都必须以 `skull_id` 为原子单位。

### 官方测试数据不可用

公开仓库明确提供了 training 数据链接，但独立 evaluation GT 的可获得性可能取决于挑战授权或已有数据包。[^2] 没有 20-skull GT 时，代码仍可做内部 Gate，但必须将结果标为 development split。

### BN calibration 污染

BN calibration 只能遍历 training loader。禁止使用 monitor、internal test 或 official test 数据更新 running statistics。

### 多 defect 相关性

100 个 case 并非 100 个独立受试者。仅报告 case-level 置信区间会低估不确定性，因此正式结论优先引用 20-skull macro 统计。

### 存储空间

训练前保留 `ckpt-last.pth` 与 `ckpt-last-bncal.pth` 即可。中间 `ckpt-epoch-*.pth` 不应长期堆积；清理前先确认训练进程已结束并将关键结果下载到本机。

## 代码清单

```text
datasets/SkullBreakDataset.py
cfgs/dataset_configs/SkullBreak.yaml
cfgs/SkullBreak_models/AdaPoinTr_implant_*.yaml
tools/prepare_skullbreak_pointcloud.py
tools/check_skullbreak_pointcloud.py
tools/test_skullbreak_data_protocol.py
scripts/run_skullbreak_implant_*.sh
scripts/eval_skullbreak_implant.sh
scripts/visualize_skullbreak_implant.sh
```

## 参考资料

[^1]: Kodym, O., Li, J., Pepe, A., et al. (2021). "SkullBreak / SkullFix - Dataset for automatic cranial implant design and a benchmark for volumetric shape learning tasks." _Data in Brief_. https://www.sciencedirect.com/science/article/pii/S2352340921001864

[^2]: Friedrich, P., Wolleb, J., Bieder, F., Thieringer, F. M., and Cattin, P. C. (2023). "Point Cloud Diffusion Models for Automatic Implant Generation - official implementation and dataset layout." _GitHub_. https://github.com/pfriedri/pcdiff-implant
