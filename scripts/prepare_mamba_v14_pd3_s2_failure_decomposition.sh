#!/usr/bin/env bash
set -euo pipefail

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
cd "$ROOT"

python tools/test_mamba_v14_pd3_s2_failure_decomposition.py
python -m py_compile \
  utils/mamba_v14_pd3_diagnostics.py \
  tools/run_mamba_v14_pd3_s2_failure_decomposition.py
bash -n scripts/run_mamba_v14_pd3_s2_failure_decomposition.sh
bash -n scripts/launch_mamba_v14_pd3_s2_failure_decomposition_tmux.sh

python - <<'PY'
import hashlib
import json
from pathlib import Path

root = Path.cwd()
protocol_path = root / "docs/mamba_v14_d4_contact_support_representation_protocol_v1.json"
protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
assert protocol["pd3"]["post_hoc"] is True
assert protocol["pd3"]["selection_inert"] is True
assert protocol["pd3"]["d3_rerun_authorized"] is False
assert protocol["protected_splits"]["all_locked"] is True

lock = json.loads((
    root / "logs/mamba_v13_d3_mug500plus/s2_head_feasibility_protocol_v1/feasibility_lock_receipt.json"
).read_text())
missing = []
for fold, item in sorted(lock["folds"].items()):
    checkpoint = root / item["s0_checkpoint"]["path"]
    if not checkpoint.is_file():
        missing.append((fold, checkpoint, item["s0_checkpoint"]["sha256"]))
        continue
    digest = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    if digest != item["s0_checkpoint"]["sha256"]:
        raise RuntimeError(f"Restored S0 checkpoint hash mismatch: {checkpoint}")

if missing:
    print("[blocked-input] restore these four frozen S0 BNCal checkpoints before replay:")
    for fold, path, digest in missing:
        print(f"  fold={fold} sha256={digest} path={path.relative_to(root)}")
    raise SystemExit(3)

print("[ok] four frozen S0 replay checkpoints are present and hash-exact")
PY

echo "[ready] P-D3 exact replay preflight passed"
echo "[next] launch scripts/launch_mamba_v14_pd3_s2_failure_decomposition_tmux.sh"
