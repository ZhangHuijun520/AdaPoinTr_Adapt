#!/usr/bin/env python
"""Runtime contract checks for S0/S1 checkpoint parity and S2 parameter scope."""

import copy
import gc
import sys
from pathlib import Path

from easydict import EasyDict

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from models.AdaPoinTr import AdaPoinTr  # noqa: E402
from utils.config import cfg_from_yaml_file  # noqa: E402


CONFIG = (
    REPO_ROOT
    / "cfgs/SkullBreak_models/"
    / "MambaAdapterV11OrderingO0_xyz_out8192_monitor.yaml"
)


def signature(model):
    state_keys = set(model.state_dict())
    parameters = sum(value.numel() for value in model.parameters())
    return state_keys, parameters


def main():
    source = cfg_from_yaml_file(str(CONFIG)).model

    s0 = AdaPoinTr(copy.deepcopy(source))
    s0_keys, s0_parameters = signature(s0)
    assert not any("rim_score_head" in key for key in s0_keys)
    del s0
    gc.collect()

    s1_config = copy.deepcopy(source)
    s1_config.dense_contact_objective = EasyDict({
        "enabled": True,
        "weight": 1.0,
        "threshold_mm": 2.0,
        "temperature_mm": 0.25,
        "tail_fraction": 0.1,
    })
    s1 = AdaPoinTr(s1_config)
    s1_keys, s1_parameters = signature(s1)
    assert s1_keys == s0_keys
    assert s1_parameters == s0_parameters
    del s1
    gc.collect()

    s2_config = copy.deepcopy(source)
    s2_config.rim_query_allocation = EasyDict({
        "enabled": True,
        "rim_queries": 32,
        "candidate_pool": 96,
        "classification_weight": 1.0,
    })
    s2 = AdaPoinTr(s2_config)
    s2_keys, s2_parameters = signature(s2)
    added = s2_keys.difference(s0_keys)
    removed = s0_keys.difference(s2_keys)
    assert added
    assert not removed
    assert all("base_model.rim_score_head" in key for key in added)
    assert s2_parameters / s0_parameters <= 1.02

    print("[ok] S0 state-dict contract remains checkpoint-compatible")
    print("[ok] S1 adds no parameters or state-dict keys")
    print("[ok] S2 only adds the preregistered rim score head")
    print(f"[ok] S2/S0 parameter ratio={s2_parameters / s0_parameters:.6f}")


if __name__ == "__main__":
    main()
