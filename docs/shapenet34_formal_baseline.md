# ShapeNet-34 AdaPoinTr Formal Baseline

This note is for running a paper-oriented ShapeNet-34 AdaPoinTr baseline on a
single RTX 4090D container after the real-data sanity run has passed.

## Direct Official Config Risk

Do not run `cfgs/ShapeNet34_models/AdaPoinTr.yaml` directly on one GPU unless
you have already confirmed the memory budget. In non-distributed mode,
`main.py` sets the training dataloader batch size to `config.total_bs`.

The official config uses:

```text
total_bs : 48
max_epoch : 600
```

On one 24G GPU, `total_bs : 48` is likely to run out of memory. The completed
sanity run used `total_bs : 2` and one pass took about 3.2 hours, so a full
600-epoch single-GPU run can take many weeks.

## Single-GPU Full Config

Use:

```text
cfgs/ShapeNet34_models/AdaPoinTr_1gpu_full.yaml
```

It keeps the official AdaPoinTr architecture and ShapeNet-34 protocol, but
uses:

```text
total_bs : 2
step_per_update : 1
max_epoch : 600
```

This is a stable single-GPU baseline configuration, not a strict reproduction
of the official multi-GPU effective batch size.

## Full Training

Start inside `tmux`:

```bash
tmux new -s shapenet34_full
```

Then run:

```bash
cd ~/adapointr_work/PoinTr
bash scripts/run_shapenet34_adapointr_1gpu_full.sh
```

Detach without stopping training:

```text
Ctrl+a then d
```

or, if the default tmux prefix is unchanged:

```text
Ctrl+b then d
```

The script writes a shell log to:

```text
logs/shapenet34_full/
```

The project logger, TensorBoard files, checkpoints, and copied config are saved
under:

```text
experiments/AdaPoinTr_1gpu_full/ShapeNet34_models/shapenet34_adapointr_1gpu_full/
```

## Short Baseline Before Full Training

Before the 600-epoch run, use the 5-epoch configuration:

```text
cfgs/ShapeNet34_models/AdaPoinTr_1gpu_5epoch.yaml
```

The runner iterates from epoch `0` through `max_epoch`, so this config uses:

```text
max_epoch : 4
```

Run:

```bash
tmux new -s shapenet34_5epoch
cd ~/adapointr_work/PoinTr
bash scripts/run_shapenet34_adapointr_1gpu_5epoch.sh
```

Outputs are saved under:

```text
logs/shapenet34_5epoch/
experiments/AdaPoinTr_1gpu_5epoch/ShapeNet34_models/shapenet34_adapointr_1gpu_5epoch/
```

After it finishes, evaluate the best checkpoint:

```bash
RUN_TAG=shapenet34_adapointr_1gpu_5epoch \
bash scripts/eval_shapenet34_adapointr_seen_unseen.sh \
  experiments/AdaPoinTr_1gpu_5epoch/ShapeNet34_models/shapenet34_adapointr_1gpu_5epoch/ckpt-best.pth
```

Use this short run to confirm that the loss curve, validation metrics,
evaluation scripts, checkpoint layout, and visualization script all behave as
expected before spending time on the full run.

## Evaluation: Seen and Unseen

After training, run all ShapeNet evaluation modes:

```bash
cd ~/adapointr_work/PoinTr
bash scripts/eval_shapenet34_adapointr_seen_unseen.sh \
  experiments/AdaPoinTr_1gpu_full/ShapeNet34_models/shapenet34_adapointr_1gpu_full/ckpt-best.pth
```

This runs:

```text
seen:   ShapeNet-34 easy, median, hard
unseen: ShapeNet-Unseen21 easy, median, hard
```

Evaluation shell logs are saved under:

```text
logs/shapenet34_eval/
```

Per-run project logs and metrics are saved under `experiments/` because
`main.py --test` creates a separate experiment directory for each mode.

## Visualization

Save sample completions for seen hard mode:

```bash
python tools/visualize_shapenet34_completion.py \
  --config cfgs/ShapeNet34_models/AdaPoinTr_1gpu_full.yaml \
  --ckpt experiments/AdaPoinTr_1gpu_full/ShapeNet34_models/shapenet34_adapointr_1gpu_full/ckpt-best.pth \
  --split seen \
  --mode hard \
  --num_samples 8
```

Save sample completions for unseen hard mode:

```bash
python tools/visualize_shapenet34_completion.py \
  --config cfgs/ShapeNetUnseen21_models/AdaPoinTr.yaml \
  --ckpt experiments/AdaPoinTr_1gpu_full/ShapeNet34_models/shapenet34_adapointr_1gpu_full/ckpt-best.pth \
  --split unseen \
  --mode hard \
  --num_samples 8
```

Outputs are saved under:

```text
experiments/visualizations/shapenet34_adapointr_1gpu_full/
```

Each sample contains:

```text
input_partial.npy / input_partial.png
missing_crop.npy
pred.npy / pred.png
gt.npy / gt.png
meta.txt
```

## Recommended Order

1. Run a 10- or 20-epoch short baseline first by copying the full config and
   changing `max_epoch`.
2. Confirm loss curves, validation metrics, checkpoint saving, and evaluation
   scripts.
3. Run the 600-epoch single-GPU full baseline only if the expected runtime is
   acceptable.
4. For strict official reproduction, use multi-GPU resources and the original
   official config.
