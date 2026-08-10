#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-adapointr-mamba}"
set -u

cd "${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

ROOT="logs/skullbreak_mamba_v12_d22_local_rim"
BASE_PROTOCOL="logs/skullbreak_mamba_v12_development/protocol_v1"
PROTOCOL="docs/mamba_v12_d22_local_rim_trust_protocol_v1.json"
AMENDMENT="docs/mamba_v12_d22_local_rim_trust_implementation_amendment_v1.json"
CONFIG_DIR="cfgs/SkullBreak_models/generated_mamba_v12_d22_local_rim_v1"

[[ -d "$BASE_PROTOCOL" ]] || {
  echo "[error] frozen development84 protocol is missing: $BASE_PROTOCOL"
  exit 2
}
[[ -f "$PROTOCOL" && -f "$AMENDMENT" ]] || {
  echo "[error] D2.2 preregistered protocol/amendment is missing"
  exit 2
}

python tools/test_mamba_v12_d22_rim_proxy.py
python tools/test_mamba_v12_d22_config_generation.py
python tools/generate_mamba_v12_d22_configs.py \
  --protocol "$PROTOCOL" \
  --amendment "$AMENDMENT" \
  --base_protocol_dir "$BASE_PROTOCOL" \
  --output_dir "$CONFIG_DIR"

python tools/verify_mamba_v12_d22_r0_zero_perturbation.py \
  --config "${CONFIG_DIR}/MambaV12D22LocalRim_R0_foldA_seed0.yaml" \
  --output "${ROOT}/preflight/r0_zero_perturbation.json" \
  --seed 0

for fold in A B C D; do
  config="${CONFIG_DIR}/MambaV12D22LocalRim_R0_fold${fold}_seed0.yaml"
  cache_dir="${ROOT}/gt_rim_cache/fold${fold}"
  python tools/prepare_mamba_v12_d22_gt_rim_cache.py \
    --config "$config" \
    --output_dir "$cache_dir" \
    --rim_band_mm 2.0
  (
    cd "$cache_dir"
    sha256sum -c files.sha256
  )
done

# A second byte-identical generation on fold A is the frozen determinism check.
python tools/prepare_mamba_v12_d22_gt_rim_cache.py \
  --config "${CONFIG_DIR}/MambaV12D22LocalRim_R0_foldA_seed0.yaml" \
  --output_dir "${ROOT}/gt_rim_cache/foldA" \
  --rim_band_mm 2.0

python - "$PROTOCOL" "$AMENDMENT" "$CONFIG_DIR" "$ROOT" <<'PY'
import hashlib
import inspect
import json
import sys
from pathlib import Path

from models.AdaPoinTr import AdaPoinTr

protocol, amendment, config_dir, root = map(Path, sys.argv[1:])
signature = inspect.signature(AdaPoinTr.forward)
if list(signature.parameters) != ["self", "xyz"]:
    raise RuntimeError(f"D2.2 changed inference interface: {signature}")

summaries = []
for fold in "ABCD":
    path = root / "gt_rim_cache" / f"fold{fold}" / "validity_summary.json"
    item = json.loads(path.read_text())
    if item["empty_cases"] != 0:
        raise RuntimeError(f"fold {fold} contains an empty GT-rim")
    if not item["reference_rim_exact_index_equivalence"]:
        raise RuntimeError(f"fold {fold} failed evaluator equivalence")
    summaries.append(item)

receipt = {
    "preflight_version": "mamba-v12-d22-preflight-v1",
    "protocol_sha256": hashlib.sha256(protocol.read_bytes()).hexdigest(),
    "amendment_sha256": hashlib.sha256(amendment.read_bytes()).hexdigest(),
    "config_manifest_sha256": hashlib.sha256(
        (config_dir / "round_a_configs_manifest.json").read_bytes()
    ).hexdigest(),
    "r0_zero_perturbation_sha256": hashlib.sha256(
        (root / "preflight" / "r0_zero_perturbation.json").read_bytes()
    ).hexdigest(),
    "fold_cases": [item["cases"] for item in summaries],
    "gt_rim_cache_files_sha256": {
        fold: hashlib.sha256(
            (root / "gt_rim_cache" / f"fold{fold}" / "files.sha256").read_bytes()
        ).hexdigest()
        for fold in "ABCD"
    },
    "empty_gt_rim_cases": 0,
    "reference_rim_exact_index_equivalence": True,
    "inference_signature": str(signature),
    "protected_splits_accessed": False,
    "candidate_training_started": False,
}
output = root / "preflight_receipt.json"
payload = (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode()
if output.exists() and output.read_bytes() != payload:
    raise RuntimeError("Refusing to overwrite a non-identical D2.2 preflight receipt")
output.parent.mkdir(parents=True, exist_ok=True)
output.write_bytes(payload)
digest = hashlib.sha256(payload).hexdigest()
Path(str(output) + ".sha256").write_text(
    f"{digest}  {output.name}\n", encoding="ascii"
)
print(f"[saved] immutable D2.2 preflight receipt: {output}")
PY

echo "[ready] D2.2 preflight passed; Round A R0 may start"
echo "[locked] confirmation20, old monitor, and official test were not accessed"
