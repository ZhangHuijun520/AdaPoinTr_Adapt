#!/usr/bin/env python
"""Static invariants for D2.2 R0/R1/R2 configuration generation."""

import tempfile
from pathlib import Path

import yaml

from generate_mamba_v12_d22_configs import generate
from generate_skullbreak_mamba_v12_dev_configs import base_config


ROOT = Path(__file__).resolve().parents[1]


def main():
    protocol = ROOT / "docs/mamba_v12_d22_local_rim_trust_protocol_v1.json"
    amendment = ROOT / (
        "docs/mamba_v12_d22_local_rim_trust_"
        "implementation_amendment_v1.json"
    )

    with tempfile.TemporaryDirectory() as temporary:
        base_protocol = Path(temporary) / "protocol"
        base_protocol.mkdir()
        for fold in "ABCD":
            (base_protocol / f"fold{fold}_train_case_ids.txt").write_text(
                f"train_{fold}\n"
            )
            (base_protocol / f"fold{fold}_dev_case_ids.txt").write_text(
                f"dev_{fold}\n"
            )
        output = Path(temporary) / "configs"
        generated = generate(protocol, amendment, base_protocol, output)
        generate(protocol, amendment, base_protocol, output)
        assert len(generated) == 13

        for fold in "ABCD":
            configs = {}
            for candidate in ("R0", "R1", "R2"):
                name = (
                    f"MambaV12D22LocalRim_{candidate}_fold{fold}_seed0.yaml"
                )
                configs[candidate] = yaml.safe_load((output / name).read_text())

            r0 = configs["R0"]
            r1 = configs["R1"]
            r2 = configs["R2"]
            assert r0["model"]["local_rim_guard"]["enabled"] is False
            assert "GT_RIM_CACHE_MANIFEST" not in r0["dataset"]["train"]["others"]
            expected_r0 = base_config(
                "o0",
                str(base_protocol / f"fold{fold}_train_case_ids.txt").replace(
                    "\\", "/"
                ),
                str(base_protocol / f"fold{fold}_dev_case_ids.txt").replace(
                    "\\", "/"
                ),
            )
            r0_without_d22 = dict(r0)
            r0_without_d22["model"] = dict(r0["model"])
            r0_without_d22["model"].pop("local_rim_guard")
            r0_without_d22.pop("development_protocol")
            assert r0_without_d22 == expected_r0
            assert r1["model"]["local_rim_guard"]["enabled"] is True
            assert r1["model"]["local_rim_guard"]["trust_enabled"] is False
            assert r2["model"]["local_rim_guard"]["trust_enabled"] is True
            assert r2["model"]["local_rim_guard"]["teacher_cache"]

            for config in configs.values():
                for split in ("train", "val", "test"):
                    dataset = config["dataset"][split]["others"]
                    assert dataset["split_field"] == "official_split"
                    assert dataset["manifest_split"] == "train"
                    assert dataset["exclude_split_field"] == "monitor_split"
                    assert dataset["exclude_manifest_split"] == "monitor"
                assert config["model"]["mamba_adapter"]["mechanism"] == "o0"
                assert config["development_protocol"][
                    "protected_splits_accessed"
                ] is False

    print("[ok] generated 12 immutable R0/R1/R2 x fold A-D configs")
    print("[ok] R0 keeps the frozen O0 loss and inference graph")
    print("[ok] R1/R2 use locked rim/teacher paths and protected splits are absent")


if __name__ == "__main__":
    main()
