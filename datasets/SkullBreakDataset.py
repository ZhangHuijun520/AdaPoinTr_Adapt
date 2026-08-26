import json
import os
import hashlib
import math

import numpy as np
import torch
import torch.utils.data as data

from .build import DATASETS


@DATASETS.register_module()
class SkullBreak(data.Dataset):
    """Point-cloud view of grouped SkullBreak defect/implant cases."""

    def __init__(self, config):
        self.data_root = os.path.abspath(os.path.expanduser(config.DATA_ROOT))
        self.asset_root = os.path.abspath(
            os.path.expanduser(str(getattr(config, "ASSET_ROOT", self.data_root)))
        )
        manifest_path = os.path.expanduser(config.MANIFEST)
        if not os.path.isabs(manifest_path):
            cwd_relative = os.path.abspath(manifest_path)
            data_relative = os.path.abspath(
                os.path.join(self.data_root, manifest_path)
            )
            manifest_path = (
                cwd_relative if os.path.isfile(cwd_relative) else data_relative
            )

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

        include_case_ids_file = getattr(
            config, "include_case_ids_file", None
        )
        self.include_case_ids_file = None
        include_case_ids = None
        include_case_ids_sha256 = None
        if include_case_ids_file is not None:
            include_path = os.path.abspath(
                os.path.expanduser(str(include_case_ids_file))
            )
            if not os.path.isfile(include_path):
                data_relative = os.path.join(
                    self.data_root,
                    os.path.expanduser(str(include_case_ids_file)),
                )
                if os.path.isfile(data_relative):
                    include_path = os.path.abspath(data_relative)
            if not os.path.isfile(include_path):
                raise FileNotFoundError(
                    "SkullBreak include-case list not found: "
                    f"{include_case_ids_file}"
                )
            with open(include_path, "rb") as handle:
                raw_include_ids = handle.read()
            include_case_ids_sha256 = hashlib.sha256(
                raw_include_ids
            ).hexdigest()
            decoded_ids = raw_include_ids.decode("utf-8").splitlines()
            include_case_ids_list = [
                item.strip()
                for item in decoded_ids
                if item.strip() and not item.lstrip().startswith("#")
            ]
            if len(include_case_ids_list) != len(set(include_case_ids_list)):
                raise ValueError(
                    "SkullBreak include-case list contains duplicate case IDs: "
                    f"{include_path}"
                )
            if not include_case_ids_list:
                raise ValueError(
                    f"SkullBreak include-case list is empty: {include_path}"
                )
            self.include_case_ids_file = include_path
            include_case_ids = set(include_case_ids_list)

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

        if include_case_ids is not None:
            eligible_case_ids = {
                str(record["case_id"]) for record in self.records
            }
            missing_case_ids = sorted(
                include_case_ids.difference(eligible_case_ids)
            )
            if missing_case_ids:
                preview = ", ".join(missing_case_ids[:10])
                raise ValueError(
                    "SkullBreak include-case list contains IDs outside the "
                    "eligible split/filter set: "
                    f"{preview}"
                )
            self.records = [
                record
                for record in self.records
                if str(record["case_id"]) in include_case_ids
            ]

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

        self._records_by_case_id = {}
        for record in self.records:
            case_id = str(record["case_id"])
            if case_id in self._records_by_case_id:
                raise ValueError(
                    "SkullBreak manifest selection contains duplicate case ID: "
                    f"{case_id}"
                )
            self._records_by_case_id[case_id] = record

        self.gt_rim_cache_manifest = getattr(
            config, "GT_RIM_CACHE_MANIFEST", None
        )
        self.gt_rim_key = getattr(config, "GT_RIM_KEY", None)
        if self.gt_rim_key is not None:
            self.gt_rim_key = str(self.gt_rim_key)
        if (
            self.gt_rim_cache_manifest is not None
            and self.gt_rim_key is not None
        ):
            raise ValueError(
                "Configure exactly one GT-rim source: "
                "GT_RIM_CACHE_MANIFEST or GT_RIM_KEY"
            )
        self._gt_rim_cache_by_case_id = None
        self._gt_rim_mask_memory = {}
        if self.gt_rim_cache_manifest is not None:
            self._load_gt_rim_cache_manifest(self.gt_rim_cache_manifest)

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
            f"input_key={self.input_key} target_key={self.target_key} "
            f"include_case_ids_file={self.include_case_ids_file} "
            f"include_sha256={include_case_ids_sha256}"
        )

    def __len__(self):
        return len(self.records)

    def __getitem__(self, idx):
        record = self.records[idx]
        point_path = self._resolve_point_path(record)

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

    def _resolve_point_path(self, record):
        point_path = os.path.expanduser(str(record["point_path"]))
        if not os.path.isabs(point_path):
            point_path = os.path.join(self.asset_root, point_path)
        point_path = os.path.abspath(point_path)
        if not os.path.isfile(point_path):
            raise FileNotFoundError(
                f"{record['case_id']}: point cloud not found: {point_path}"
            )
        return point_path

    def get_case_normalization(self, case_id):
        """Return validated normalization metadata for one manifest case."""

        case_id = str(case_id)
        record = self._records_by_case_id.get(case_id)
        if record is None:
            raise KeyError(f"Unknown SkullBreak case ID: {case_id}")

        normalization = record.get("normalization")
        if not isinstance(normalization, dict):
            raise ValueError(
                f"{case_id}: manifest normalization metadata is missing"
            )

        centroid = np.asarray(normalization.get("centroid"), dtype=np.float64)
        try:
            scale = float(normalization.get("scale"))
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"{case_id}: normalization.scale must be a finite positive scalar"
            ) from exc

        if centroid.shape != (3,) or not np.isfinite(centroid).all():
            raise ValueError(
                f"{case_id}: normalization.centroid must contain 3 finite values"
            )
        if not np.isfinite(scale) or scale <= 0:
            raise ValueError(
                f"{case_id}: normalization.scale must be finite and positive, "
                f"got {scale}"
            )

        return {
            "centroid": centroid.copy(),
            "scale": scale,
        }

    def get_normalization_scales(self, case_ids, device=None, dtype=None):
        """Return per-case normalized-to-world scale factors in manifest order."""

        if dtype is None:
            dtype = torch.float32
        scales = [
            self.get_case_normalization(case_id)["scale"]
            for case_id in case_ids
        ]
        return torch.tensor(scales, device=device, dtype=dtype)

    def _load_gt_rim_cache_manifest(self, manifest_path):
        manifest_path = os.path.abspath(os.path.expanduser(str(manifest_path)))
        if not os.path.isfile(manifest_path):
            raise FileNotFoundError(
                f"SkullBreak GT-rim cache manifest not found: {manifest_path}"
            )
        hashes_path = os.path.join(os.path.dirname(manifest_path), "files.sha256")
        if not os.path.isfile(hashes_path):
            raise FileNotFoundError(
                f"SkullBreak GT-rim cache hash manifest not found: {hashes_path}"
            )
        expected_manifest_hash = None
        with open(hashes_path, "r", encoding="ascii") as handle:
            for line in handle:
                fields = line.split()
                if len(fields) == 2 and fields[1].lstrip("*") == os.path.basename(
                    manifest_path
                ):
                    expected_manifest_hash = fields[0]
                    break
        if expected_manifest_hash is None:
            raise ValueError("GT-rim files.sha256 omits its cache manifest")
        with open(manifest_path, "rb") as handle:
            actual_manifest_hash = hashlib.sha256(handle.read()).hexdigest()
        if actual_manifest_hash != expected_manifest_hash:
            raise ValueError("SkullBreak GT-rim cache manifest SHA256 mismatch")

        entries = {}
        with open(manifest_path, "r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                line = line.strip()
                if not line:
                    continue
                entry = json.loads(line)
                case_id = str(entry.get("case_id", ""))
                if not case_id or case_id in entries:
                    raise ValueError(
                        "Invalid or duplicate GT-rim cache case ID at line "
                        f"{line_number}: {case_id!r}"
                    )
                mask_path = os.path.expanduser(str(entry.get("mask_path", "")))
                if not os.path.isabs(mask_path):
                    mask_path = os.path.join(
                        os.path.dirname(manifest_path), mask_path
                    )
                entry = dict(entry)
                entry["mask_path"] = os.path.abspath(mask_path)
                entries[case_id] = entry

        selected = set(self._records_by_case_id)
        missing = sorted(selected.difference(entries))
        extra = sorted(set(entries).difference(selected))
        if missing or extra:
            raise ValueError(
                "GT-rim cache case set differs from selected SkullBreak cases: "
                f"missing={missing[:10]} extra={extra[:10]}"
            )
        for case_id, entry in entries.items():
            manifest_scale = self.get_case_normalization(case_id)["scale"]
            cached_scale = float(entry.get("normalization_scale", float("nan")))
            if not math.isclose(
                manifest_scale,
                cached_scale,
                rel_tol=0.0,
                abs_tol=1.0e-12,
            ):
                raise ValueError(f"{case_id}: GT-rim cache scale mismatch")
        self.gt_rim_cache_manifest = manifest_path
        self._gt_rim_cache_by_case_id = entries

    def get_gt_rim_masks(self, case_ids, device=None):
        """Load deterministic all-point GT-rim masks for a training batch."""

        if self._gt_rim_cache_by_case_id is None and self.gt_rim_key is None:
            raise RuntimeError("SkullBreak GT-rim supervision is not configured")

        masks = []
        for case_id in case_ids:
            case_id = str(case_id)
            if case_id in self._gt_rim_mask_memory:
                masks.append(self._gt_rim_mask_memory[case_id])
                continue
            if self.gt_rim_key is not None:
                record = self._records_by_case_id.get(case_id)
                if record is None:
                    raise KeyError(f"Unknown SkullBreak case ID: {case_id}")
                point_path = self._resolve_point_path(record)
                with np.load(point_path, allow_pickle=False) as sample:
                    if self.gt_rim_key not in sample:
                        raise KeyError(
                            f"{case_id}: NPZ has no GT-rim key "
                            f"{self.gt_rim_key!r}"
                        )
                    mask = sample[self.gt_rim_key].copy()
                expected_count = record.get("point_audit", {}).get(
                    "reference_rim_points"
                )
            else:
                entry = self._gt_rim_cache_by_case_id.get(case_id)
                if entry is None:
                    raise KeyError(f"GT-rim cache has no entry for {case_id}")
                mask_path = entry["mask_path"]
                if not os.path.isfile(mask_path):
                    raise FileNotFoundError(
                        f"{case_id}: GT-rim mask not found: {mask_path}"
                    )
                expected_hash = str(entry.get("mask_sha256", ""))
                with open(mask_path, "rb") as handle:
                    payload = handle.read()
                actual_hash = hashlib.sha256(payload).hexdigest()
                if actual_hash != expected_hash:
                    raise ValueError(
                        f"{case_id}: GT-rim mask SHA256 mismatch"
                    )
                mask = np.load(mask_path, allow_pickle=False)
                expected_count = entry.get("rim_points", -1)
            if mask.shape != (self.npartial,) or mask.dtype != np.bool_:
                raise ValueError(
                    f"{case_id}: invalid GT-rim mask shape/dtype "
                    f"{mask.shape}/{mask.dtype}"
                )
            if (
                expected_count is not None
                and int(mask.sum()) != int(expected_count)
            ):
                raise ValueError(f"{case_id}: GT-rim point count mismatch")
            if not mask.any():
                raise ValueError(f"{case_id}: cached GT-rim mask is empty")
            tensor = torch.from_numpy(mask.copy())
            self._gt_rim_mask_memory[case_id] = tensor
            masks.append(tensor)

        return torch.stack(masks, dim=0).to(device=device)
