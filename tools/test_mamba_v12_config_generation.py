#!/usr/bin/env python
"""Synthetic checks for Round-A config generation."""

import json
import tempfile
from pathlib import Path

import yaml

from generate_skullbreak_mamba_v12_dev_configs import CANDIDATES, generate
from lock_skullbreak_mamba_v12_development_protocol import (
    EXPECTED_DEFECT_TYPES,
    render_outputs,
    write_locked,
)


def main():
    strict = []
    for skull_index in range(104):
        for defect_type in sorted(EXPECTED_DEFECT_TYPES):
            strict.append({
                "case_id": f"train__{skull_index:03d}__{defect_type}",
                "skull_id": f"train:{skull_index:03d}",
                "defect_type": defect_type,
                "official_split": "train",
                "monitor_split": "train",
            })
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        protocol_dir = root / "protocol"
        config_dir = root / "configs"
        write_locked(render_outputs(strict, "synthetic"), protocol_dir)
        generated = generate(protocol_dir, config_dir)
        assert len(generated) == 17
        for candidate, mechanism in CANDIDATES.items():
            for fold in "ABCD":
                path = config_dir / f"MambaV12Dev_{candidate}_fold{fold}_seed0.yaml"
                config = yaml.safe_load(path.read_text())
                assert config["model"]["mamba_adapter"]["mechanism"] == mechanism
                for split in ("train", "val", "test"):
                    others = config["dataset"][split]["others"]
                    assert others["manifest_split"] == "train"
                    assert others["exclude_manifest_split"] == "monitor"
                    assert "include_case_ids_file" in others
                assert config["development_protocol"]["official_test_allowed"] is False
        manifest = json.loads(
            (config_dir / "round_a_configs_manifest.json").read_text()
        )
        assert manifest["num_configs"] == 16
        generate(protocol_dir, config_dir)
    print("[ok] generated 16 immutable C0-C3 x fold A-D configs")
    print("[ok] val/test aliases remain inside each new development fold")
    print("[ok] old monitor and official test are absent")


if __name__ == "__main__":
    main()
