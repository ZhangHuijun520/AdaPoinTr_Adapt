# Server Setup for AdaPoinTr

This guide prepares a Linux/CUDA server for real AdaPoinTr experiments. Unlike
the local Windows toy setup, server training should use the official compiled
CUDA extensions, not the PyTorch fallbacks.

## Files

Server setup files added for this project:

```text
environment_server.yml
scripts/setup_server_env.sh
docs/server_setup.md
```

Related local smoke-test documentation:

```text
docs/local_smoke_test.md
```

## Recommended Server Assumptions

Recommended baseline:

```text
OS: Linux
GPU: NVIDIA CUDA-capable GPU
Driver: supports CUDA 11.8 runtime or newer
Python: 3.9
PyTorch: 2.1.x + CUDA 11.8
```

The provided `environment_server.yml` uses:

```text
pytorch=2.1.*
torchvision=0.16.*
pytorch-cuda=11.8
```

If your server uses a different CUDA runtime, edit `pytorch-cuda=11.8` before
creating the environment. For example, use `pytorch-cuda=12.1` on a CUDA 12.1
setup if your driver and cluster modules support it.

## Create Conda Environment

From the repository root:

```bash
conda env create -f environment_server.yml
conda activate adapointr-server
```

Check PyTorch and CUDA:

```bash
python - <<'PY'
import torch
print(torch.__version__)
print(torch.version.cuda)
print(torch.cuda.is_available())
print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else "no cuda")
PY
```

Expected:

```text
torch.cuda.is_available() -> True
```

## Install Official CUDA Extensions

Run:

```bash
bash scripts/setup_server_env.sh
```

This installs and verifies:

- `extensions/chamfer_dist`
- `extensions/emd`
- official `pointnet2_ops`

It intentionally skips GRNet-only extensions by default:

- `extensions/cubic_feature_sampling`
- `extensions/gridding`
- `extensions/gridding_loss`

To build those optional GRNet extensions too:

```bash
INSTALL_GRNET_EXTENSIONS=1 bash scripts/setup_server_env.sh
```

If the build machine cannot infer the CUDA architecture, set it manually before
running the script. Examples:

```bash
export TORCH_CUDA_ARCH_LIST="7.5"       # Turing
export TORCH_CUDA_ARCH_LIST="8.0"       # A100
export TORCH_CUDA_ARCH_LIST="8.6"       # RTX 30 series / A10
export TORCH_CUDA_ARCH_LIST="8.9"       # RTX 40 series / L40
```

## Required Verification

After extension installation, this command must print `False`:

```bash
python -c "from utils import pointnet2_utils; print(pointnet2_utils.using_fallback())"
```

Expected:

```text
False
```

If it prints `True`, the official `pointnet2_ops` package was not installed or
is not importable. Do not start real training until this is fixed.

## Server Toy Dry Run

Before full dataset training, run the same toy dry run on the server:

```bash
python tools/toy_smoke_adapointr.py
```

Then run the official training entrypoint:

```bash
python main.py \
  --config cfgs/ToyPCN_models/AdaPoinTr.yaml \
  --exp_name server_toy_smoke \
  --num_workers 0 \
  --val_freq 1
```

Expected outputs:

```text
toy_smoke_adapointr.py -> toy smoke ok
main.py -> train, validation, checkpoint save
```

The toy output directory should be:

```text
experiments/AdaPoinTr/ToyPCN_models/server_toy_smoke/
```

## Test Saved Toy Checkpoint

```bash
python main.py \
  --test \
  --config cfgs/ToyPCN_models/AdaPoinTr.yaml \
  --ckpts experiments/AdaPoinTr/ToyPCN_models/server_toy_smoke/ckpt-last.pth \
  --exp_name server_toy_smoke_eval \
  --num_workers 0
```

This confirms checkpoint loading and test-mode evaluation.

## Then Move to Real Baselines

Once the server toy dry run passes:

1. Prepare PCN or Projected-ShapeNet.
2. Run official AdaPoinTr baseline without model changes.
3. Save logs, config, and checkpoint paths.
4. Only after the baseline is stable, start Mamba module integration.

## Troubleshooting

If `pointnet2_ops` fails to build:

- confirm `nvcc --version` works;
- confirm GCC is compatible with the installed CUDA toolkit;
- set `TORCH_CUDA_ARCH_LIST`;
- try a cleaner PyTorch/CUDA pairing, such as PyTorch 2.1 + CUDA 11.8.

If Chamfer or EMD fails to import:

- rerun `bash scripts/setup_server_env.sh`;
- confirm the active Conda env is `adapointr-server`;
- avoid installing extensions with a different Python executable.

If `models.GRNet` prints an optional import warning:

```text
[models] skip optional import models.GRNet: No module named 'gridding'
```

This is acceptable for AdaPoinTr. Build optional GRNet extensions only if you
need GRNet experiments.
