import json
import os

import numpy as np
import torch
import torch.utils.data as data

from .build import DATASETS


@DATASETS.register_module()
class SkullFix(data.Dataset):
    """Point-cloud view of paired SkullFix defective/complete skulls."""

    def __init__(self, config):
        self.data_root = os.path.abspath(os.path.expanduser(config.DATA_ROOT))
        manifest_path = os.path.expanduser(config.MANIFEST)
        if not os.path.isabs(manifest_path):
            manifest_path = os.path.join(self.data_root, manifest_path)

        self.subset = str(config.subset)
        self.manifest_split = str(getattr(config, "manifest_split", self.subset))
        self.npoints = int(config.N_POINTS)
        self.npartial = int(config.N_PARTIAL)
        self.cars = False
        self.taxonomy_id = str(getattr(config, "TAXONOMY_ID", "skullfix"))

        max_samples = getattr(config, "max_samples", getattr(config, "MAX_SAMPLES", None))
        self.max_samples = None if max_samples is None else int(max_samples)

        if not os.path.isfile(manifest_path):
            raise FileNotFoundError(
                f"SkullFix manifest not found: {manifest_path}. "
                "Run tools/prepare_skullfix_pointcloud.py first."
            )

        self.records = []
        with open(manifest_path, "r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                if record.get("split") != self.manifest_split:
                    continue
                if "case_id" not in record or "point_path" not in record:
                    raise ValueError(
                        f"Invalid SkullFix manifest record at line {line_number}: "
                        "case_id and point_path are required."
                    )
                self.records.append(record)

        self.records.sort(key=lambda item: item["case_id"])
        if self.max_samples is not None:
            self.records = self.records[: self.max_samples]
        if not self.records:
            raise ValueError(
                f"No SkullFix records found for manifest split '{self.manifest_split}' "
                f"in {manifest_path}."
            )

        print(
            f"[DATASET] SkullFix subset={self.subset} "
            f"manifest_split={self.manifest_split} samples={len(self.records)}"
        )

    def __len__(self):
        return len(self.records)

    def __getitem__(self, idx):
        record = self.records[idx]
        point_path = record["point_path"]
        if not os.path.isabs(point_path):
            point_path = os.path.join(self.data_root, point_path)

        with np.load(point_path, allow_pickle=False) as sample:
            partial = sample["partial"].astype(np.float32, copy=False)
            gt = sample["gt"].astype(np.float32, copy=False)

        if partial.shape != (self.npartial, 3):
            raise ValueError(
                f"{record['case_id']}: expected partial shape "
                f"({self.npartial}, 3), got {partial.shape}"
            )
        if gt.shape != (self.npoints, 3):
            raise ValueError(
                f"{record['case_id']}: expected gt shape "
                f"({self.npoints}, 3), got {gt.shape}"
            )
        if not np.isfinite(partial).all() or not np.isfinite(gt).all():
            raise ValueError(f"{record['case_id']}: point cloud contains NaN or Inf")

        return (
            self.taxonomy_id,
            str(record["case_id"]),
            (torch.from_numpy(partial.copy()), torch.from_numpy(gt.copy())),
        )

    def get_record(self, idx):
        return dict(self.records[idx])
