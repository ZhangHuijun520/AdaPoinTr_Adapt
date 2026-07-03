# SkullFix AdaPoinTr-Implant Baseline Protocol

本协议用于把实验目标从完整颅骨补全切换为植入体/缺损区域预测：

```text
input  = defective skull point cloud
target = implant / defect-region point cloud
output = predicted implant point cloud
final reconstruction = defective skull union predicted implant
```

## Evaluation Metrics

主指标只评价 `predicted implant` 与 `GT implant`，并且全部在原始物理坐标系中以毫米为单位计算：

- `CD-L1 / ASSD [mm]`：越低越好。
- `HD95 [mm]`：越低越好，用于约束局部异常偏差。
- `NSD@1mm` 与 `NSD@2mm`：越高越好，作为点云版 Surface Dice / BDSC 近似。
- `Pred->Ref mean [mm]` 与 `Ref->Pred mean [mm]`：用于分解过度生成和覆盖不足。

辅助指标评价 `defective skull union predicted implant` 与 `GT complete skull`：

- `final CD-L1 / ASSD [mm]`
- `final HD95 [mm]`
- `final NSD@1mm / NSD@2mm`

完整论文阶段如果生成体素/网格，再补充：

- `DSC`
- `BDSC / Surface Dice`
- `Volume Error / RVE`
- `Boundary / Rim fitting error`
- `Inference time / GPU memory / params / FLOPs`

## Implementation Decisions

旧的 complete-skull 实验保留。新的 implant baseline 使用：

- `SkullFixDataset.target_key = implant`
- `N_POINTS = 4096`
- `N_PARTIAL = 8192`
- `AdaPoinTr.num_points = 4096`
- `AdaPoinTr.num_query = 256`
- `query_selection = learned_only`
- `denoise_weight = 0.0`

`learned_only` 的原因：implant 是缺损区域点云，不应把 coarse query 锚定到 defective skull 表面，否则会复现 complete-skull overfit 中发现的覆盖偏差。

## Three Gates Before Full Training

### Gate 1: Implant Sanity

目标：确认数据、模型前后向、4096 点输出、日志和 checkpoint 都能跑通。

```bash
cd ~/adapointr_work/PoinTr
chmod +x scripts/run_skullfix_implant_sanity.sh
tmux new -s skullfix_implant_sanity
bash scripts/run_skullfix_implant_sanity.sh
```

通过标准：

- 训练入口无报错。
- 产生 `ckpt-best.pth`、`ckpt-last.pth`。
- 日志里显示 `target_key=implant`、`N_POINTS=4096` 对应的训练可运行。

### Gate 2: One-Sample Implant Overfit

目标：确认 AdaPoinTr-Implant 至少能学习一个固定病例的 implant。

```bash
cd ~/adapointr_work/PoinTr
chmod +x scripts/run_skullfix_implant_overfit1.sh
tmux new -s skullfix_implant_overfit1
bash scripts/run_skullfix_implant_overfit1.sh
```

评估：

```bash
cd ~/adapointr_work/PoinTr
CKPT=experiments/AdaPoinTr_implant_overfit1/SkullFix_models/skullfix_implant_overfit1/ckpt-best.pth

CONFIG=cfgs/SkullFix_models/AdaPoinTr_implant_overfit1.yaml \
SPLIT=test \
OUT_DIR=logs/skullfix_implant_eval/overfit1 \
bash scripts/eval_skullfix_implant.sh "$CKPT"

CONFIG=cfgs/SkullFix_models/AdaPoinTr_implant_overfit1.yaml \
SPLIT=test \
NUM_SAMPLES=1 \
OUT_DIR=experiments/visualizations/skullfix_implant_overfit1 \
bash scripts/visualize_skullfix_implant.sh "$CKPT"
```

通过标准：

- `implant CD-L1 [mm]` 明显下降。
- `implant Ref->Pred mean [mm]` 不再表现出严重覆盖不足。
- 可视化中的 `prediction_implant.png` 与 `ground_truth_implant.png` 大体位置、轮廓相符。

### Gate 3: Small-Subset Baseline

目标：确认短训练、test evaluation、可视化和结果落盘的完整闭环可用。

```bash
cd ~/adapointr_work/PoinTr
chmod +x scripts/run_skullfix_implant_small.sh
tmux new -s skullfix_implant_small
bash scripts/run_skullfix_implant_small.sh
```

评估与可视化：

```bash
cd ~/adapointr_work/PoinTr
CKPT=experiments/AdaPoinTr_implant_small/SkullFix_models/skullfix_implant_small/ckpt-best.pth

bash scripts/eval_skullfix_implant.sh "$CKPT"
bash scripts/visualize_skullfix_implant.sh "$CKPT"
```

通过标准：

- `logs/skullfix_implant_eval/*summary.json` 和 `*_per_sample.csv` 正常保存。
- `experiments/visualizations/skullfix_implant_small/*` 中有：
  - `input_defective.png`
  - `prediction_implant.png`
  - `ground_truth_implant.png`
  - `final_reconstruction.png`
  - `ground_truth_complete.png`
  - `meta.json`
- 指标与可视化方向一致。

## Full Baseline After Gates

三道 gate 通过后，再把 `cfgs/SkullFix_models/AdaPoinTr_implant_small.yaml` 扩展为全量 SkullFix 训练配置。SkullBreak 后续应沿用同一数据字段、同一归一化还原、同一 evaluator 和同一可视化格式，确保 AdaPoinTr baseline 与 Mamba 改进模型公平对比。

## Extended evaluation after the full baseline

The point evaluator now reports, for every metric:

- per-case values in CSV;
- mean, sample standard deviation, median, quartiles, range;
- bootstrap confidence interval for the mean;
- paired final-reconstruction versus defective-input deltas;
- point-sampled contact-rim CD, HD95, NSD, and GT-rim-to-prediction gap.

Predictions can be exported for voxel evaluation:

```bash
CONFIG=cfgs/SkullFix_models/AdaPoinTr_implant_full100_bncal.yaml \
SPLIT=test \
OUT_DIR=logs/skullfix_implant_eval/full100_extended_test \
SAVE_PREDICTIONS_DIR=logs/skullfix_implant_eval/full100_predictions_test \
bash scripts/eval_skullfix_implant.sh \
  experiments/AdaPoinTr_implant_full100_bncal/SkullFix_models/skullfix_implant_full100_bncal/ckpt-last-bncal.pth
```

`tools/evaluate_skullfix_voxel_metrics.py` requires the original SkullFix NRRD
files. It maps each normalized prediction back to the original physical grid,
uses a fixed-radius surface splat, and then computes:

- implant and final-reconstruction DSC;
- voxel-surface ASSD and HD95 in millimeters;
- Surface Dice at the configured physical tolerances;
- signed relative volume error;
- voxel-derived contact-rim metrics.

Example:

```bash
python tools/evaluate_skullfix_voxel_metrics.py \
  --prediction_manifest \
    logs/skullfix_implant_eval/full100_predictions_test/predictions_manifest.jsonl \
  --raw_root /path/to/original/SkullFix \
  --out_dir logs/skullfix_implant_eval/full100_voxel_test \
  --splat_radius_mm 1.0 \
  --rim_band_mm 2.0
```

The DSC value depends on the point-to-voxel conversion. It must therefore be
reported as voxelized-prediction DSC together with the splat radius. It is not
directly comparable with a native voxel-output model unless that model is
evaluated under the same conversion protocol. Surface Dice is based on
surface-voxel counts; for anisotropic grids, this is not an area-weighted mesh
Surface Dice.
