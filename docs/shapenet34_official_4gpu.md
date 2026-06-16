# ShapeNet-34 AdaPoinTr Official 4GPU Run

This workflow runs the official ShapeNet-34 AdaPoinTr configuration:

```text
cfgs/ShapeNet34_models/AdaPoinTr.yaml
total_bs : 48
max_epoch : 600
```

On 4 GPUs, DDP uses per-GPU batch size `48 / 4 = 12`.

## Training

Start a tmux session:

```bash
tmux new -s shapenet34_official_4gpu
```

Run:

```bash
cd ~/adapointr_work/PoinTr
bash scripts/run_shapenet34_adapointr_official_4gpu.sh
```

Detach:

```text
Ctrl+a then d
```

or:

```text
Ctrl+b then d
```

The script automatically resumes from:

```text
experiments/AdaPoinTr/ShapeNet34_models/shapenet34_adapointr_official_full_4gpu/ckpt-last.pth
```

if it exists.

Training logs:

```text
logs/shapenet34_official_4gpu/
experiments/AdaPoinTr/ShapeNet34_models/shapenet34_adapointr_official_full_4gpu/
```

Progress bars are displayed with `tqdm` on rank 0.

## Evaluation

After training:

```bash
cd ~/adapointr_work/PoinTr
bash scripts/eval_shapenet34_official_seen_unseen.sh \
  experiments/AdaPoinTr/ShapeNet34_models/shapenet34_adapointr_official_full_4gpu/ckpt-best.pth
```

This evaluates:

```text
seen:   easy / median / hard
unseen: easy / median / hard
```

Evaluation logs:

```text
logs/shapenet34_official_eval/
experiments/AdaPoinTr/ShapeNet34_models/test_shapenet34_adapointr_official_full_4gpu_seen_*/
experiments/AdaPoinTr/ShapeNetUnseen21_models/test_shapenet34_adapointr_official_full_4gpu_unseen_*/
```

## Visualization

Save seen-hard and unseen-hard examples:

```bash
cd ~/adapointr_work/PoinTr
bash scripts/visualize_shapenet34_official.sh \
  experiments/AdaPoinTr/ShapeNet34_models/shapenet34_adapointr_official_full_4gpu/ckpt-best.pth
```

Outputs:

```text
experiments/visualizations/shapenet34_official_full_4gpu/seen_hard/
experiments/visualizations/shapenet34_official_full_4gpu/unseen_hard/
```
