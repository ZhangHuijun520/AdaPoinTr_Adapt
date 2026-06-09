#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

echo "[setup] repo: ${ROOT_DIR}"
echo "[setup] python: $(command -v python)"

python - <<'PY'
import sys
import torch

print(f"[setup] python version: {sys.version.split()[0]}")
print(f"[setup] torch version: {torch.__version__}")
print(f"[setup] torch cuda: {torch.version.cuda}")
print(f"[setup] cuda available: {torch.cuda.is_available()}")
if not torch.cuda.is_available():
    raise SystemExit("[setup] ERROR: CUDA is not available. Check driver, CUDA runtime, and PyTorch install.")
print(f"[setup] gpu: {torch.cuda.get_device_name(0)}")
PY

if command -v nvcc >/dev/null 2>&1; then
    echo "[setup] nvcc:"
    nvcc --version
else
    echo "[setup] WARNING: nvcc was not found on PATH. CUDA extension compilation may fail."
fi

if [[ -n "${TORCH_CUDA_ARCH_LIST:-}" ]]; then
    echo "[setup] TORCH_CUDA_ARCH_LIST=${TORCH_CUDA_ARCH_LIST}"
else
    echo "[setup] TORCH_CUDA_ARCH_LIST is not set; PyTorch will infer architectures from visible GPUs."
fi

echo "[setup] upgrading build helpers"
python -m pip install --upgrade pip setuptools wheel ninja

echo "[setup] installing Python requirements"
python -m pip install \
    easydict \
    h5py \
    matplotlib \
    "numpy<2" \
    "open3d>=0.18" \
    opencv-python \
    pyyaml \
    scipy \
    tensorboardX \
    timm==0.4.5 \
    tqdm \
    transforms3d \
    einops

echo "[setup] building Chamfer Distance extension"
pushd extensions/chamfer_dist >/dev/null
python setup.py install
popd >/dev/null

echo "[setup] building EMD extension"
pushd extensions/emd >/dev/null
python setup.py install
popd >/dev/null

echo "[setup] installing PointNet++ ops"
python -m pip install \
    "git+https://github.com/erikwijmans/Pointnet2_PyTorch.git#egg=pointnet2_ops&subdirectory=pointnet2_ops_lib"

if [[ "${INSTALL_GRNET_EXTENSIONS:-0}" == "1" ]]; then
    echo "[setup] INSTALL_GRNET_EXTENSIONS=1; building optional GRNet extensions"
    for ext in cubic_feature_sampling gridding gridding_loss; do
        pushd "extensions/${ext}" >/dev/null
        python setup.py install
        popd >/dev/null
    done
else
    echo "[setup] skipping optional GRNet extensions. Set INSTALL_GRNET_EXTENSIONS=1 to build them."
fi

echo "[setup] verifying compiled extension path"
python - <<'PY'
import torch
from utils import pointnet2_utils
from extensions.chamfer_dist import ChamferDistanceL1
from extensions.emd import emd_module as emd

print(f"[verify] pointnet2 using fallback: {pointnet2_utils.using_fallback()}")
if pointnet2_utils.using_fallback():
    raise SystemExit("[verify] ERROR: pointnet2_ops is not installed; official server training must not use fallback.")

xyz = torch.rand(1, 128, 3, device="cuda")
fps_idx = pointnet2_utils.furthest_point_sample(xyz, 16)
print(f"[verify] pointnet2 fps: shape={tuple(fps_idx.shape)}, device={fps_idx.device}")

a = torch.rand(1, 64, 3, device="cuda", requires_grad=True)
b = torch.rand(1, 64, 3, device="cuda")
loss = ChamferDistanceL1()(a, b)
loss.backward()
print(f"[verify] chamfer loss: {loss.item():.6f}")

ea = torch.rand(1, 1024, 3, device="cuda")
eb = torch.rand(1, 1024, 3, device="cuda")
dist, assignment = emd.emdModule()(ea, eb, 0.005, 50)
print(f"[verify] emd: dist_shape={tuple(dist.shape)}, assignment_shape={tuple(assignment.shape)}")
PY

echo "[setup] server CUDA extension setup complete"
