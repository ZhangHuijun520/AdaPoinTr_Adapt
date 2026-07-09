# SkullFix AdaPoinTr-Implant Point-Count Ablation Protocol

This protocol tests whether the current `8192 input / 4096 implant output`
baseline is limited by point density before changing the model architecture.

## Step 1: GT Sampling Upper Bound

Goal: estimate how well a point-only implant can represent the raw GT implant
mask at different sampling densities.

Run on the server if raw SkullFix NRRD files are available there:

```bash
cd ~/adapointr_work/PoinTr
conda activate adapointr-server

RAW_ROOT=/path/to/raw/SkullFix \
MANIFEST=data/SkullFixPC/manifest.jsonl \
DATA_ROOT=data/SkullFixPC \
SPLIT=test \
COUNTS=1024,2048,4096,8192,16384 \
bash scripts/run_skullfix_gt_sampling_upper_bound.sh
```

Outputs:

- `logs/skullfix_implant_point_count/gt_sampling_upper_bound/skullfix_gt_sampling_test.csv`
- `logs/skullfix_implant_point_count/gt_sampling_upper_bound/skullfix_gt_sampling_test_summary.json`

Interpretation:

- If GT-4096 has low DSC / Surface Dice or large RVE, 4096 output points are a
  representation bottleneck.
- If GT-4096 is already close to GT-8192/16384, the bottleneck is more likely
  model learning or local boundary alignment.

## Step 2: Output-Only Ablation

Goal: increase only the target/output density from 4096 to 8192 while keeping
the defective-skull input at 8192.

First prepare an 8192-implant SkullFix point-cloud pack:

```bash
cd ~/adapointr_work/PoinTr
conda activate adapointr-server

RAW_ROOT=/path/to/raw/SkullFix \
OUT_ROOT=~/datasets/SkullFixPC_out8192 \
bash scripts/prepare_skullfix_pc_out8192.sh
```

Then train/evaluate:

```bash
tmux new -s skullfix_out8192
cd ~/adapointr_work/PoinTr
conda activate adapointr-server

bash scripts/run_skullfix_implant_full100_out8192_bncal.sh
```

Main outputs:

- `experiments/AdaPoinTr_implant_full100_out8192_bncal/.../ckpt-last-bncal.pth`
- `logs/skullfix_implant_point_count/full100_out8192_bncal_test/`
- `logs/skullfix_implant_point_count/full100_out8192_predictions_test/`
- `experiments/visualizations/skullfix_implant_full100_out8192_bncal_test/`

Compare against the frozen baseline:

- baseline: `8192 input / 4096 output`
- ablation: `8192 input / 8192 output`

Primary metrics:

- implant CD / HD95 / NSD
- implant voxel DSC / Surface Dice / RVE
- rim contact CD / HD95 / NSD
- final reconstruction metrics only as secondary evidence

## Step 3: Global + Rim-Local Input

Goal: test whether denser local boundary input helps beyond simply increasing
the output density.

Prepare a point-cloud pack with `8192` global defective points plus `2048`
defective-skull rim-local points:

```bash
cd ~/adapointr_work/PoinTr
conda activate adapointr-server

RAW_ROOT=/path/to/raw/SkullFix \
OUT_ROOT=~/datasets/SkullFixPC_out8192_rim2048 \
RIM_BAND_MM=2.0 \
bash scripts/prepare_skullfix_pc_out8192_rim2048.sh
```

Then train/evaluate:

```bash
tmux new -s skullfix_out8192_rim2048
cd ~/adapointr_work/PoinTr
conda activate adapointr-server

bash scripts/run_skullfix_implant_full100_out8192_rim2048_bncal.sh
```

This configuration uses:

- input key: `partial_global_rim`
- input points: `8192 + 2048 = 10240`
- target/output implant points: `8192`

Important caveat:

The first rim-local implementation samples defective-skull points close to the
GT implant surface during point-cloud preparation. Treat this as a controlled
upper-bound / diagnostic input-enhancement experiment unless a non-leaky rim
extractor from the defective skull alone is added later.

## Recommended Decision Rule

1. If Step 1 shows GT-4096 is a strong bottleneck and Step 2 improves voxel
   metrics, use 8192 implant output for future Mamba comparisons.
2. If Step 2 improves little but Step 3 improves rim/contact metrics, prioritize
   defect-local or rim-aware input modeling.
3. If neither Step 2 nor Step 3 improves much, keep the frozen baseline protocol
   and move to architecture-level Mamba experiments.
