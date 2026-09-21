#!/usr/bin/env python
"""Non-executing L1 contract checks for Cranial-SCQR v1.1."""

import ast
import importlib.util
import json
import sys
import tempfile
import types
from pathlib import Path
from types import SimpleNamespace

import yaml

from generate_cranial_scqr_v11_configs import ROOT, VARIANTS, generate


SOURCE_FILES = (
    ROOT / "models/cranial_scqr/__init__.py",
    ROOT / "models/cranial_scqr/local_geometry.py",
    ROOT / "models/cranial_scqr/contact_support.py",
    ROOT / "models/cranial_scqr/query_conditioning.py",
    ROOT / "models/AdaPoinTr.py",
    ROOT / "tools/runner.py",
    ROOT / "tools/generate_cranial_scqr_v11_configs.py",
)


def _syntax_check():
    for path in SOURCE_FILES:
        source = path.read_text(encoding="utf-8")
        ast.parse(source, filename=str(path))
        compile(source, str(path), "exec")


def _load_scqr_package_without_models_side_effects():
    package_name = "_cranial_scqr_l1_static"
    package_dir = ROOT / "models/cranial_scqr"
    package = types.ModuleType(package_name)
    package.__path__ = [str(package_dir)]
    package.__package__ = package_name
    sys.modules[package_name] = package
    for leaf in ("local_geometry", "contact_support", "query_conditioning"):
        name = f"{package_name}.{leaf}"
        spec = importlib.util.spec_from_file_location(name, package_dir / f"{leaf}.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    spec = importlib.util.spec_from_file_location(
        package_name,
        package_dir / "__init__.py",
        submodule_search_locations=[str(package_dir)],
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[package_name] = module
    spec.loader.exec_module(module)
    return module


def _namespace(mapping):
    return SimpleNamespace(**mapping)


def _contract_check(scqr):
    assert scqr.VARIANT_MATRIX == {
        key: {
            "enabled": values[0],
            "local_geometry_enabled": values[1],
            "contact_supervision_enabled": values[2],
            "query_conditioning_enabled": values[3],
            "contact_bias_beta": values[4],
        }
        for key, values in VARIANTS.items()
    }
    legacy = scqr.validate_scqr_config(
        None,
        embed_dim=384,
        num_query=256,
        center_num=[512, 256],
        denoise_weight=0.5,
    )
    assert legacy.variant == "B0" and legacy.enabled is False
    for variant, values in VARIANTS.items():
        block = {
            "variant": variant,
            "enabled": values[0],
            "local_geometry_enabled": values[1],
            "contact_supervision_enabled": values[2],
            "query_conditioning_enabled": values[3],
            "contact_bias_beta": values[4],
            "local_knn_small": 16,
            "local_knn_large": 32,
            "attention_dim": 128,
            "warmup_epochs": 20,
            "rim_band_mm": 2.0,
            "alpha_local_init": 0.01,
            "alpha_query_init": 0.01,
            "attention_dropout": 0.0,
            "probability_floor": 1.0e-4,
            "initialization_seed": 31001,
            "auxiliary_loss_weight": None,
        }
        contract = scqr.validate_scqr_config(
            _namespace(block),
            embed_dim=384,
            num_query=256,
            center_num=[512, 256],
            denoise_weight=0.0,
        )
        assert contract.variant == variant
        assert contract.auxiliary_loss_weight is None


def _source_contract_check():
    local = (ROOT / "models/cranial_scqr/local_geometry.py").read_text()
    contact = (ROOT / "models/cranial_scqr/contact_support.py").read_text()
    query = (ROOT / "models/cranial_scqr/query_conditioning.py").read_text()
    ada = (ROOT / "models/AdaPoinTr.py").read_text()
    runner = (ROOT / "tools/runner.py").read_text()
    combined_new = local + contact + query
    assert "nn.BatchNorm" not in combined_new
    assert "nn.Dropout" not in combined_new
    assert "stable=True" in local and "k=self.large_k" in local
    assert "nn.Linear(4, 32)" in local and "nn.Linear(256, 128)" in local
    assert "torch.no_grad()" in contact
    assert "positive.any()" in contact and "negative.any()" in contact
    assert "contact_probability.detach().float()" in query
    assert "torch.softmax(logits, dim=-1)" in query
    assert "self.base_model(xyz, epoch=epoch)" in ada
    assert "self._condition_scqr_queries(q, x, pe, scqr_aux, epoch)" in ada
    assert "build_contact_support_labels(" in ada
    assert runner.index("\n    _enforce_scqr_execution_guard(config)") < runner.index(
        "builder.dataset_builder(args, config.dataset.train)"
    )
    assert "ret = base_model(partial, epoch=epoch)" in runner


def _config_check():
    with tempfile.TemporaryDirectory() as temporary:
        output = Path(temporary) / "configs"
        generated = generate(output)
        generate(output)
        assert len(generated) == 9
        manifest = json.loads((output / "l1_configs_manifest.json").read_text())
        assert manifest["num_configs"] == 8
        assert manifest["execution_lock"]["training_authorized"] is False
        assert manifest["protected_payload_accessed"] is False
        for fold in "AB":
            models = {}
            for variant, values in VARIANTS.items():
                name = f"CranialSCQRV11_{variant}_fold{fold}_seed0.yaml"
                config = yaml.safe_load((output / name).read_text())
                models[variant] = config["model"]
                assert config["cranial_scqr_execution"]["training_authorized"] is False
                assert config["cranial_scqr_execution"]["optimizer_steps_authorized"] == 0
                assert config["model"]["cranial_scqr"]["auxiliary_loss_weight"] is None
                assert config["model"]["cranial_scqr"]["contact_bias_beta"] == values[4]
                assert config["model"]["mamba_adapter"]["enabled"] is False
                assert config["model"]["denoise_weight"] == 0.0
                assert config["model"]["center_num"] == [512, 256]
                assert config["model"]["num_query"] == 256
                for split in ("train", "val", "test"):
                    dataset = config["dataset"][split]["others"]
                    assert dataset["manifest_split"] == "train"
                    assert dataset["exclude_manifest_split"] == "monitor"
                    assert dataset["input_key"] == "partial"
                    assert dataset["target_key"] == "implant"
                rendered = (output / name).read_text().lower()
                assert "confirmation20" not in rendered
                assert "official_split: test" not in rendered
                assert "mug500" not in rendered
            common = {}
            for variant, model in models.items():
                common[variant] = dict(model)
                common[variant].pop("cranial_scqr")
            assert len({yaml.safe_dump(value) for value in common.values()}) == 1


def main():
    _syntax_check()
    scqr = _load_scqr_package_without_models_side_effects()
    _contract_check(scqr)
    _source_contract_check()
    _config_check()
    print("[ok] source syntax and isolated SCQR imports")
    print("[ok] frozen B0/A1/Q0/QC mechanism matrix and legacy-disabled path")
    print("[ok] 8 immutable A/B seed-0 configs; all execution permissions locked")
    print("[ok] no model/tensor forward, dataset payload, GPU, BNCal, or timing")


if __name__ == "__main__":
    main()
