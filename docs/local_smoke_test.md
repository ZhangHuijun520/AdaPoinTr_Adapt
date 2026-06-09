# Local Toy Smoke Test

This document captures the known-good local setup for running AdaPoinTr through
the official training entrypoint on a tiny synthetic dataset. It is intended as a
checkpoint before model changes such as Mamba modules are introduced.

## Goal

The local machine is not intended for full PCN, ShapeNet, or medical point cloud
training. The goal here is narrower:

- import the AdaPoinTr codebase successfully;
- build a Dataset and DataLoader through the official registry;
- run AdaPoinTr forward and backward;
- run `main.py` through train, validation, checkpoint save, and test mode.

## Local Environment

Known working local environment:

```text
Conda env: adapointr
Python: 3.9.21
PyTorch: 2.5.1
PyTorch CUDA: 11.8
GPU: NVIDIA GeForce RTX 3050 Ti Laptop GPU
```

Activate or call the environment with:

```powershell
conda activate adapointr
```

or:

```powershell
conda run -n adapointr python <script.py>
```

## Why Fallbacks Exist

On the local Windows machine, compiling the official CUDA extensions failed
because CUDA 11.8 is incompatible with the installed newer VS 2022 STL:

```text
error STL1002: Unexpected compiler version, expected CUDA 12.4 or newer.
```

For local smoke tests only, the repo contains small PyTorch fallbacks:

- `utils/pointnet2_utils.py`
  - Uses official `pointnet2_ops` if it is installed.
  - Falls back to PyTorch implementations of FPS, gather, grouping, 3-NN,
    3-interpolate, and ball query.
- `extensions/chamfer_dist/__init__.py`
  - Uses the compiled `chamfer` extension if available.
  - Falls back to `torch.cdist` for tiny point clouds.
- `extensions/emd/emd_module.py`
  - Uses the compiled `emd` extension if available.
  - Falls back to nearest-neighbor distances for smoke-test compatibility.

These fallbacks are slow and not suitable for real experiments. On a server,
install the official CUDA extensions and confirm that `utils.pointnet2_utils`
uses the compiled backend:

```bash
python -c "from utils import pointnet2_utils; print(pointnet2_utils.using_fallback())"
```

Expected server output after installing official `pointnet2_ops`:

```text
False
```

Expected local output on this Windows machine:

```text
True
```

## Toy Dataset

The synthetic toy dataset is implemented in:

```text
datasets/ToyPCNDataset.py
```

It registers `ToyPCN` and returns the same shape as the PCN dataset:

```python
taxonomy_id, model_id, (partial, gt)
```

Default toy config:

```text
cfgs/dataset_configs/ToyPCN.yaml
```

Current tiny settings:

```text
N_POINTS: 128
N_PARTIAL: 96
NUM_SAMPLES_TRAIN: 4
NUM_SAMPLES_VAL: 10
NUM_SAMPLES_TEST: 10
```

`N_PARTIAL` must stay at least `64`, because AdaPoinTr samples 64 denoising
points in the training branch.

## Toy AdaPoinTr Config

The tiny AdaPoinTr config is:

```text
cfgs/ToyPCN_models/AdaPoinTr.yaml
```

It reduces the model to a very small version:

```text
num_query: 16
num_points: 128
center_num: [16, 8]
embed_dim: 64
encoder depth: 1
decoder depth: 1
total_bs: 1
max_epoch: 0
```

This config is not meaningful for performance. It is only a pipeline test.

## Fast Forward/Backward Check

Run the direct model smoke test:

```powershell
cd C:\Users\zhj\Documents\Codex\2026-06-06\mamba-ccf-c-1-high-resolution\work\PoinTr
conda run -n adapointr python tools\toy_smoke_adapointr.py
```

Known-good output:

```text
toy smoke ok | loss=1.145168 | max_cuda_mem=75.9 MB
```

This verifies model construction, forward, loss, backward, and one optimizer
step without using the full training runner.

## Official Training Entrypoint

Run toy training through `main.py`:

```powershell
cd C:\Users\zhj\Documents\Codex\2026-06-06\mamba-ccf-c-1-high-resolution\work\PoinTr
conda run -n adapointr python main.py --config cfgs/ToyPCN_models/AdaPoinTr.yaml --exp_name toy_smoke --num_workers 0 --val_freq 1
```

This should complete:

- one tiny training epoch (`max_epoch: 0`);
- validation on the toy validation split;
- checkpoint saves.

Expected checkpoint directory:

```text
experiments/AdaPoinTr/ToyPCN_models/toy_smoke/
```

Expected checkpoint files:

```text
ckpt-best.pth
ckpt-last.pth
ckpt-epoch-000.pth
```

## Official Test Mode

Run test mode from the saved checkpoint:

```powershell
conda run -n adapointr python main.py --test --config cfgs/ToyPCN_models/AdaPoinTr.yaml --ckpts .\experiments\AdaPoinTr\ToyPCN_models\toy_smoke\ckpt-last.pth --exp_name toy_smoke_eval --num_workers 0
```

This verifies that checkpoint loading and the official test branch also work
with `ToyPCN`.

## Server Notes

For real training on PCN, Projected-ShapeNet, SkullBreak/SkullFix, or medical
point clouds:

1. Use a Linux/CUDA server when possible.
2. Install official compiled extensions:
   - `extensions/chamfer_dist`
   - `extensions/emd`
   - `pointnet2_ops`
3. Confirm `pointnet2_utils.using_fallback()` returns `False`.
4. Do not report metrics produced by local fallback kernels.
5. Keep `ToyPCN` only as a dry-run dataset.

The next safe step after this checkpoint is to prepare a server environment file
and run the same toy config on the server before full dataset training.
