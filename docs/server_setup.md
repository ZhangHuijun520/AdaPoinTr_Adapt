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

## Ziqiang 5000 Image Choice

For this PoinTr/AdaPoinTr setup, prefer the platform image:

```text
NoteBook PyTorch (CUDA) Full V1.5.0
NVIDIA driver 535.120.03, CUDA 11.8.9, cuDNN 8.9.0
```

This is the first choice because it matches `environment_server.yml`
(`pytorch-cuda=11.8`) and is the lower-risk stack for the older CUDA extensions
used by PoinTr:

- `extensions/chamfer_dist`
- `extensions/emd`
- official `pointnet2_ops`

For a 4090 container, set the architecture before building extensions:

```bash
export TORCH_CUDA_ARCH_LIST="8.9"
```

Use the CUDA 12.4 image only if the CUDA 11.8 PyTorch image is missing required
developer tools such as `nvcc`, or if the cluster administrator recommends it.
If you switch to CUDA 12.4, update the environment file to a matching PyTorch
CUDA build, for example `pytorch-cuda=12.4`, and expect a higher chance that
legacy CUDA extensions may need small build patches.

cuDNN is not the deciding factor for this project. AdaPoinTr depends more on a
consistent PyTorch/CUDA/compiler stack for custom point-cloud CUDA operators.

## Ziqiang 5000 Platform Notes

From the platform manuals:

- GPU containers are managed through Kubernetes. Billing starts when the
  container status becomes running and stops after the container is destroyed.
- The user directory is persistent and shared across containers under the same
  account. Put uploaded files, this repository, Conda environments, datasets,
  checkpoints, and logs under the user directory.
- The platform does not support normal user-level `apt` or `apt-get` installs.
  Prefer Conda, pip, and source builds installed inside the user directory.
- Terminal upload can upload files; file and directory operations such as
  creating, deleting, and renaming should be done inside the terminal.
- Use `nvidia-smi` to check GPU visibility and memory usage.
- For long jobs, use `nohup` and redirect logs so terminal closure does not hide
  output:

```bash
nohup python main.py --config cfgs/ToyPCN_models/AdaPoinTr.yaml \
  --exp_name server_toy_smoke --num_workers 0 --val_freq 1 \
  > server_toy_smoke.log 2>&1 &

tail -f server_toy_smoke.log
```

For TensorBoard or Jupyter-style services, start the service inside the
container on a fixed internal port, then create a platform port-forwarding rule
for that internal port. Example:

```bash
tensorboard --logdir experiments --host 0.0.0.0 --port 8000
```

The manual says forwarded services are available for campus-network access; use
the platform-provided forwarded address/port.

## Create Conda Environment

From the repository root:

```bash
conda env create -f environment_server.yml
conda activate adapointr-server
```

If Conda is killed while solving the full environment file, create a smaller
environment first and install PyTorch with pip:

```bash
conda create -n adapointr-server python=3.9 pip -y
conda activate adapointr-server

python -m pip install --upgrade pip "setuptools<70" wheel ninja
python -m pip install torch==2.1.2+cu118 torchvision==0.16.2+cu118 \
  --index-url https://download.pytorch.org/whl/cu118
python -m pip install numpy==1.26.4 h5py matplotlib scipy pyyaml tqdm \
  easydict tensorboardX timm==0.4.5 transforms3d einops opencv-python \
  "open3d>=0.18"
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

If the server cannot access GitHub, install `pointnet2_ops` from an offline
source package:

```bash
rm -rf third_party/pointnet2_ops_lib
mkdir -p third_party/pointnet2_ops_lib

python - <<'PY'
from pathlib import Path
import shutil
import zipfile

zip_path = Path.home() / "pointnet2_ops_lib.zip"
out_dir = Path("third_party/pointnet2_ops_lib")
out_dir.mkdir(parents=True, exist_ok=True)

with zipfile.ZipFile(zip_path) as zf:
    for info in zf.infolist():
        name = info.filename.replace("\\", "/").lstrip("/")
        if not name or name.endswith("/"):
            continue
        target = out_dir / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with zf.open(info) as src, open(target, "wb") as dst:
            shutil.copyfileobj(src, dst)

print("extract done")
PY

python - <<'PY'
from pathlib import Path

p = Path("third_party/pointnet2_ops_lib/setup.py")
s = p.read_text()
s = s.replace(
    'os.environ["TORCH_CUDA_ARCH_LIST"] = "3.7+PTX;5.0;6.0;6.1;6.2;7.0;7.5"',
    'os.environ.setdefault("TORCH_CUDA_ARCH_LIST", "8.9")',
)
p.write_text(s)
print("patched setup.py")
PY

python -m pip install --no-build-isolation third_party/pointnet2_ops_lib
```

After this, rerun verification or the whole setup script:

```bash
bash scripts/setup_server_env.sh
```

Do not use plain `python -m zipfile -e` for zip files created on Windows if
paths appear with backslashes like `pointnet2_ops\_version.py`; normalize the
paths with the extraction script above.

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

## Verified Ziqiang 5000 Smoke Test

The following stack has been verified on a 1-GPU RTX 4090 D container:

```text
Python: 3.9.23
PyTorch: 2.1.2+cu118
torch.version.cuda: 11.8
nvcc: 11.8
GPU: NVIDIA GeForce RTX 4090 D
TORCH_CUDA_ARCH_LIST: 8.9
```

Verified checks:

```text
pointnet2_utils.using_fallback() -> False
tools/toy_smoke_adapointr.py -> toy smoke ok
main.py ToyPCN training -> train, validation, checkpoint save
main.py --test ToyPCN checkpoint -> TEST RESULTS
```

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

If importing Open3D fails with a system library error such as:

```text
OSError: libX11.so.6: cannot open shared object file
```

do not use `apt` on Ziqiang 5000. This project lazily imports Open3D only for
`.pcd/.ply` files and falls back to a PyTorch implementation for F-Score, so
ToyPCN and common `.npy/.h5/.txt` training paths can run without loading Open3D.
Use non-Open3D data formats or ask the platform administrator to provide the
missing system libraries if `.pcd/.ply` support is required.

If test mode fails in EMD with:

```text
AssertionError: assert(n % 1024 == 0)
```

the toy point count is too small for the official EMD CUDA kernel. This project
skips EMD and returns `0` when the compared point count is not a multiple of
1024, which is acceptable for ToyPCN smoke tests. Real completion benchmarks
should keep the official benchmark point counts.

If `models.GRNet` prints an optional import warning:

```text
[models] skip optional import models.GRNet: No module named 'gridding'
```

This is acceptable for AdaPoinTr. Build optional GRNet extensions only if you
need GRNet experiments.
