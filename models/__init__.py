from .build import build_model_from_cfg


def _try_import(module_name):
    try:
        __import__(module_name)
    except ImportError as exc:
        print(f"[models] skip optional import {module_name}: {exc}")


_try_import("models.TopNet")
_try_import("models.PoinTr")
_try_import("models.GRNet")
_try_import("models.PCN")
_try_import("models.FoldingNet")
_try_import("models.SnowFlakeNet")
_try_import("models.AdaPoinTr")
