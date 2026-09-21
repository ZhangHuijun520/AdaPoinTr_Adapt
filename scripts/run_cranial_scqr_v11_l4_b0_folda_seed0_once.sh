#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="/home/jovyan/adapointr_work/PoinTr"
PYTHON="/opt/conda/envs/adapointr-mamba/bin/python"
RUNTIME="$ROOT/cfgs/SkullBreak_models/cranial_scqr_v11_l4_round_a_authorized_v1/CranialSCQRV11_B0_foldA_seed0.yaml"
RUN_ID="cranial_scqr_v11_B0_foldA_seed0_v1_20260911T160850Z"
MASTER="$ROOT/logs/cranial_scqr_v11/l4_round_a/$RUN_ID"
EXPERIMENT="$ROOT/experiments/CranialSCQRV11_B0_foldA_seed0/cranial_scqr_v11_l4_round_a_authorized_v1/$RUN_ID"

cd "$ROOT"
test -d "$MASTER"
record_exit() {
  status="$?"
  printf '%s\n' "$status" > "$MASTER/exit_code"
  date -u +%Y-%m-%dT%H:%M:%SZ > "$MASTER/finished_at_utc.txt"
}
trap record_exit EXIT
printf '%s\n' "$$" > "$MASTER/pid"
date -u +%Y-%m-%dT%H:%M:%SZ > "$MASTER/started_at_utc.txt"
test ! -e "$EXPERIMENT"
test ! -e "$ROOT/experiments/CranialSCQRV11_B0_foldA_seed0/cranial_scqr_v11_l4_round_a_authorized_v1/TFBoard/$RUN_ID"

echo "b1b805708b41b48377fa58854936a4895db3561cb819c6e9917bbc42e1435702  $RUNTIME" | sha256sum -c -
echo "1fe833d43cba1a76efcf71050e456319034a678779959b4cda2b190f95cb0f0c  docs/cranial_scqr_v1_research_2026_09_10/l4_b0_folda_seed0_training_authorization_receipt_v1.json" | sha256sum -c -
echo "b7044f4f24e2f0b4a1e38a9d4ca466f2bb8168ffe1a0ad864b3e1c8f1c3f0fe9  docs/cranial_scqr_v1_research_2026_09_10/l4_round_a_training_protocol_v1.json" | sha256sum -c -
echo "07d6b9b05ada5549d8ed4781f57f31c1655e50eb5917583cd0f4e9b151b61804  tools/runner.py" | sha256sum -c -
echo "b913eab4e5c779dd22adf029d2ed6f97a0f477e96fb090ca6e4d5975c69bd031  tools/cranial_scqr_l4_audit.py" | sha256sum -c -
echo "c6e4c4a67f6ebf684be618cec7eb9568d775cfb03205773fc901883516939102  tools/run_cranial_scqr_v11_l4_bncal.py" | sha256sum -c -
echo "06cc0ef6a8a882956aa3136d57f999a1a9a945213c73f92c2f3026121b076dbd  logs/skullbreak_mamba_v12_development/protocol_v1/foldA_train_case_ids.txt" | sha256sum -c -

GPU_COUNT="$(nvidia-smi --query-gpu=uuid --format=csv,noheader | wc -l)"
read -r GPU_USED GPU_TOTAL < <(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits | tr -d ',' | awk 'NR==1 {print $1, $2}')
GPU_FREE="$((GPU_TOTAL - GPU_USED))"
DISK_FREE_KIB="$(df -Pk /home/jovyan | awk 'NR==2 {print $4}')"
if [[ "$GPU_COUNT" -ne 1 || "$GPU_FREE" -lt 22000 ]]; then
  echo "[blocked] GPU launch budget failed: count=$GPU_COUNT free_mib=$GPU_FREE" >&2
  exit 20
fi
if [[ "$DISK_FREE_KIB" -lt 8388608 ]]; then
  echo "[blocked] disk launch budget failed: free_kib=$DISK_FREE_KIB" >&2
  exit 21
fi

"$PYTHON" - "$MASTER/prelaunch_environment.json" "$GPU_USED" "$GPU_TOTAL" "$DISK_FREE_KIB" <<'PY'
import json, platform, socket, sys
from datetime import datetime, timezone
from pathlib import Path
import torch
out, used, total, disk = sys.argv[1:]
payload = {
    "status": "LAUNCH_READY",
    "checked_at_utc": datetime.now(timezone.utc).isoformat(),
    "hostname": socket.gethostname(),
    "platform": platform.platform(),
    "python": sys.version,
    "torch": torch.__version__,
    "cuda_runtime": torch.version.cuda,
    "cudnn": torch.backends.cudnn.version(),
    "gpu_memory_used_mib": int(used),
    "gpu_memory_total_mib": int(total),
    "disk_free_kib": int(disk),
    "runtime_config_sha256": "b1b805708b41b48377fa58854936a4895db3561cb819c6e9917bbc42e1435702",
    "optimizer_steps_before_launch": 0,
}
Path(out).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

echo "[stage] training start $(date -u +%Y-%m-%dT%H:%M:%SZ)"
CUDA_VISIBLE_DEVICES=0 "$PYTHON" -u main.py \
  --config "$RUNTIME" \
  --launcher none \
  --num_workers 4 \
  --seed 0 \
  --deterministic \
  --val_freq 101 \
  --exp_name "$RUN_ID"

"$PYTHON" - "$EXPERIMENT/l4_execution_state.json" <<'PY'
import json, sys
from pathlib import Path
x=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert x["status"] == "training_complete_pending_bncal"
assert x["optimizer_steps"] == x["model_updates"] == 3939
assert x["epoch_traversals_completed"] == 101
assert x["development_payload_accessed"] is False
assert x["bncal_updates"] == 0
print("[verified] training counts and dev lock")
PY

echo "[stage] BNCal start $(date -u +%Y-%m-%dT%H:%M:%SZ)"
CUDA_VISIBLE_DEVICES=0 "$PYTHON" -u tools/run_cranial_scqr_v11_l4_bncal.py \
  --config "$RUNTIME" \
  --experiment_dir "$EXPERIMENT" \
  --batch_size 8 \
  --num_workers 0 \
  --seed 0

(cd "$EXPERIMENT" && sha256sum -c l4_bncal_files.sha256)
"$PYTHON" - "$MASTER/run_completion_receipt.json" "$EXPERIMENT" "$RUNTIME" <<'PY'
import hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path
out, experiment, runtime = map(Path, sys.argv[1:])
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
training = json.loads((experiment / "l4_execution_state.json").read_text())
bncal = json.loads((experiment / "l4_bncal_receipt.json").read_text())
assert training["status"] == "training_complete_pending_bncal"
assert bncal["status"] == "PASS"
assert bncal["optimizer_steps"] == bncal["model_parameter_updates"] == 0
assert bncal["payload_open_events"] == 315
assert bncal["bncal_batches"] == 40
assert bncal["npz_members_opened"] == ["partial"]
payload = {
    "receipt_version": "cranial-scqr-v1.1-L4-B0-foldA-seed0-completion-v1",
    "status": "TRAINING_AND_BNCAL_PASS",
    "finished_at_utc": datetime.now(timezone.utc).isoformat(),
    "run_key": "B0_foldA_seed0",
    "runtime_config_sha256": sha(runtime),
    "optimizer_steps": training["optimizer_steps"],
    "epoch_traversals": training["epoch_traversals_completed"],
    "training_checkpoint_sha256": sha(experiment / "ckpt-last.pth"),
    "bncal_checkpoint_sha256": sha(experiment / "ckpt-last-bncal.pth"),
    "training_state_sha256": sha(experiment / "l4_execution_state.json"),
    "bncal_receipt_sha256": sha(experiment / "l4_bncal_receipt.json"),
    "development_payload_accessed": False,
    "automatic_next_run_authorized": False,
    "development_evaluation_authorized": False,
}
out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("[done] TRAINING_AND_BNCAL_PASS")
PY

echo "[stage] complete $(date -u +%Y-%m-%dT%H:%M:%SZ)"
