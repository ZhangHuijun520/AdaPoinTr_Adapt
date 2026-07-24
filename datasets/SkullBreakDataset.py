import json
import os

import numpy as np
import torch
import torch.utils.data as data

from .build import DATASETS


@DATASETS.register_module()
class SkullBreak(data.Dataset):
    """Point-cloud view of grouped SkullBreak defect/implant cases."""

    def __init__(self, config):
        self.data_root = os.path.abspath(os.path.expanduser(config.DATA_ROOT))
        manifest_path = os.path.expanduser(config.MANIFEST)
        if not os.path.isabs(manifest_path):
            manifest_path = os.path.join(self.data_root, manifest_path)

        self.subset = str(config.subset)
        self.split_field = str(getattr(config, "split_field", "official_split"))
        self.manifest_split = str(
            getattr(config, "manifest_split", self.subset)
        )
        exclude_split_field = getattr(config, "exclude_split_field", None)
        exclude_manifest_split = getattr(
            config, "exclude_manifest_split", None
        )
        if (exclude_split_field is None) != (exclude_manifest_split is None):
            raise ValueError(
                "SkullBreak exclude_split_field and "
                "exclude_manifest_split must be configured together"
            )
        self.exclude_split_field = (
            None
            if exclude_split_field is None
            else str(exclude_split_field)
        )
        self.exclude_manifest_split = (
            None
            if exclude_manifest_split is None
            else str(exclude_manifest_split)
        )
        self.npoints = int(config.N_POINTS)
        self.npartial = int(config.N_PARTIAL)
        self.cars = False
        self.taxonomy_id = str(
            getattr(config, "TAXONOMY_ID", "skullbreak")
        )
        self.input_key = str(getattr(config, "input_key", "partial")).lower()
        if self.input_key not in {"partial", "gt", "implant"}:
            raise ValueError(
                "SkullBreak input_key must be 'partial', 'gt', or 'implant', "
                f"got {self.input_key!r}"
            )
        self.target_key = str(getattr(config, "target_key", "gt")).lower()
        if self.target_key not in {"gt", "implant"}:
            raise ValueError(
                "SkullBreak target_key must be 'gt' or 'implant', "
                f"got {self.target_key!r}"
            )

        max_samples = getattr(
            config, "max_samples", getattr(config, "MAX_SAMPLES", None)
        )
        max_skulls = getattr(
            config, "max_skulls", getattr(config, "MAX_SKULLS", None)
        )
        self.max_samples = None if max_samples is None else int(max_samples)
        self.max_skulls = None if max_skulls is None else int(max_skulls)
        self.repeat = int(getattr(config, "repeat", 1))
        if self.repeat < 1:
            raise ValueError(
                f"SkullBreak repeat must be >= 1, got {self.repeat}"
            )
        if self.max_skulls is not None and self.max_skulls < 1:
            raise ValueError("SkullBreak max_skulls must be positive")

        if not os.path.isfile(manifest_path):
            raise FileNotFoundError(
                f"SkullBreak manifest not found: {manifest_path}. "
                "Run tools/prepare_skullbreak_pointcloud.py first."
            )

        self.records = []
        with open(manifest_path, "r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                if record.get(self.split_field) != self.manifest_split:
                    continue
                if (
                    self.exclude_split_field is not None
                    and record.get(self.exclude_split_field)
                    == self.exclude_manifest_split
                ):
                    continue
                required = {"case_id", "skull_id", "point_path"}
                missing = required.difference(record)
                if missing:
                    raise ValueError(
                        "Invalid SkullBreak manifest record at line "
                        f"{line_number}: missing {sorted(missing)}."
                    )
                self.records.append(record)

        self.records.sort(
            key=lambda item: (
                str(item["skull_id"]),
                str(item.get("defect_type", "")),
                str(item["case_id"]),
            )
        )
        if self.max_skulls is not None:
            selected_skulls = []
            for record in self.records:
                skull_id = str(record["skull_id"])
                if skull_id not in selected_skulls:
                    selected_skulls.append(skull_id)
                if len(selected_skulls) == self.max_skulls:
                    break
            selected = set(selected_skulls)
            self.records = [
                record
                for record in self.records
                if str(record["skull_id"]) in selected
            ]
        if self.max_samples is not None:
            self.records = self.records[: self.max_samples]
        if not self.records:
            raise ValueError(
                "No SkullBreak records found for "
                f"{self.split_field}={self.manifest_split!r} "
                f"in {manifest_path}."
            )

        unique_samples = len(self.records)
        unique_skulls = len(
            {str(record["skull_id"]) for record in self.records}
        )
        if self.repeat > 1:
            self.records = self.records * self.repeat

        print(
            f"[DATASET] SkullBreak subset={self.subset} "
            f"{self.split_field}={self.manifest_split} "
            f"exclude={self.exclude_split_field}="
            f"{self.exclude_manifest_split} "
            f"samples={len(self.records)} unique_samples={unique_samples} "
            f"unique_skulls={unique_skulls} repeat={self.repeat} "
            f"input_key={self.input_key} target_key={self.target_key}"
        )

    def __len__(self):
        return len(self.records)

    def __getitem__(self, idx):
        record = self.records[idx]
        point_path = record["point_path"]
        if not os.path.isabs(point_path):
            point_path = os.path.join(self.data_root, point_path)

        with np.load(point_path, allow_pickle=False) as sample:
            partial = sample[self.input_key].astype(
                np.float32, copy=False
            )
            gt = sample[self.target_key].astype(np.float32, copy=False)

        if partial.shape != (self.npartial, 3):
            raise ValueError(
                f"{record['case_id']}: expected {self.input_key} input shape "
                f"({self.npartial}, 3), got {partial.shape}"
            )
        if gt.shape != (self.npoints, 3):
            raise ValueError(
                f"{record['case_id']}: expected {self.target_key} target shape "
                f"({self.npoints}, 3), got {gt.shape}"
            )
        if not np.isfinite(partial).all() or not np.isfinite(gt).all():
            raise ValueError(
                f"{record['case_id']}: point cloud contains NaN or Inf"
            )

        return (
            self.taxonomy_id,
            str(record["case_id"]),
            (torch.from_numpy(partial.copy()), torch.from_numpy(gt.copy())),
        )

    def get_record(self, idx):
        return dict(self.records[idx])
