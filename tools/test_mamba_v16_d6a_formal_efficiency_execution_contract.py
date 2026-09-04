#!/usr/bin/env python3
"""Contract tests for D6-A formal-efficiency authorization and execution."""

from __future__ import annotations

import inspect
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.authorize_mamba_v16_d6a_formal_efficiency_execution import validate_protocol  # noqa: E402
from utils.mamba_d6a_efficiency import (  # noqa: E402
    LATENCY_RATIO_MAXIMUM,
    PEAK_MEMORY_RATIO_MAXIMUM,
    TIMED_RUNS,
    WARMUP_RUNS,
    benchmark_candidate,
)


def main() -> None:
    protocol_path = ROOT / "docs/mamba_v16_d6a_formal_efficiency_execution_authorization_protocol_v1.json"
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    validate_protocol(protocol)
    assert WARMUP_RUNS == 10 and TIMED_RUNS == 50
    assert LATENCY_RATIO_MAXIMUM == 1.15
    assert PEAK_MEMORY_RATIO_MAXIMUM == 1.10
    signature = inspect.signature(benchmark_candidate)
    assert signature.parameters["warmup_runs"].default == 10
    assert signature.parameters["timed_runs"].default == 50

    runner = (ROOT / "tools/run_mamba_v16_d6a_formal_efficiency.py").read_text(encoding="utf-8")
    preflight = (ROOT / "tools/preflight_mamba_v16_d6a_formal_efficiency_execution.py").read_text(encoding="utf-8")
    assert 'for candidate in ("R0", "R1")' in runner
    assert "del model" in runner and "torch.cuda.empty_cache()" in runner
    assert "benchmark_candidate(candidate, model, descriptors)" in runner
    assert '"formal_warmup_runs": 0' in preflight
    assert '"formal_timed_runs": 0' in preflight
    for source in (runner, preflight):
        assert "optimizer.step" not in source
        assert "torch.optim" not in source
        assert "MUG500plusD6Development400" not in source
        assert "proposal_confirmation" in source
    print("[ok] R0-then-R1, one-model residency and frozen 10/50 benchmark are fixed")
    print("[ok] authorization preflight cannot execute the formal benchmark")
    print("[ok] formal result cannot automatically authorize training")
    print("[locked] training=false seed1=false confirmation=false D6B=false sealed=false")


if __name__ == "__main__":
    main()
