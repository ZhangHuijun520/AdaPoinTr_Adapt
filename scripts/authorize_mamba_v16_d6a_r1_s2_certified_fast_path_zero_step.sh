#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

LOCK="${D6_R1_S2_PROTOCOL_LOCK_DIR:-$ROOT/logs/mamba_v16_d6_contact_support/d6a_r1_s2_certified_fast_path_feasibility_protocol_v1}"
CONFIG="${D6_R1_S2_ZERO_STEP_CONFIG_DIR:-$ROOT/cfgs/MUG500plus_models/generated_mamba_v16_d6a_r1_s2_certified_fast_path_zero_step_authorized_v1}"
AUTH="${D6_R1_S2_ZERO_STEP_AUTH_DIR:-$ROOT/logs/mamba_v16_d6_contact_support/d6a_r1_s2_certified_fast_path_zero_step_authorization_v1}"

echo "===== D6-A R1 S2 implementation and zero-step contract tests ====="
python tools/test_mamba_v16_d6a_r1_s2_certified_fast_path_zero_step.py

echo "===== Issue isolated S2 artificial zero-step authorization ====="
python tools/authorize_mamba_v16_d6a_r1_s2_certified_fast_path_zero_step.py \
  --protocol_lock_dir "$LOCK" \
  --config_output_dir "$CONFIG" \
  --authorization_output_dir "$AUTH"

echo "===== Verify immutable S2 authorization ====="
(
  cd "$AUTH"
  sha256sum -c files.sha256
)

python - "$CONFIG" "$AUTH" <<'PY'
import importlib.util
import sys
from pathlib import Path

root = Path.cwd()
path = root / "tools/verify_mamba_v16_d6a_r1_s2_certified_fast_path_zero_step_authorization.py"
spec = importlib.util.spec_from_file_location("d6_s2_zero_step_verify", path)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)
module.verify_authorization(Path(sys.argv[1]), Path(sys.argv[2]))
print("[ok] isolated S2 implementation and artificial zero-step authorization verified")
PY

echo "[authorized-next] one 168-case artificial CUDA equivalence/routing zero-step only"
echo "[locked] timing=false benchmark=false production=false formal_rerun=false training=false D6B=false sealed=false"
