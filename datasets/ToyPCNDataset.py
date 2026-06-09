import numpy as np
import torch
import torch.utils.data as data

from .build import DATASETS


@DATASETS.register_module()
class ToyPCN(data.Dataset):
    """Small synthetic PCN-style completion dataset for local smoke tests.

    It returns the same tuple shape as PCN: taxonomy_id, model_id, (partial, gt).
    The samples are generated deterministically, so no files need to be stored.
    """

    def __init__(self, config):
        self.subset = config.subset
        self.npoints = int(config.N_POINTS)
        self.npartial = int(getattr(config, "N_PARTIAL", max(96, self.npoints // 2)))
        self.cars = bool(getattr(config, "CARS", False))
        self.taxonomy_id = str(getattr(config, "TAXONOMY_ID", "02691156"))
        self.taxonomy_name = str(getattr(config, "TAXONOMY_NAME", "toy_ellipsoid"))
        self.seed = int(getattr(config, "SEED", 20260609))
        self.noise_std = float(getattr(config, "NOISE_STD", 0.002))

        if self.npartial < 64:
            raise ValueError("ToyPCN needs N_PARTIAL >= 64 because AdaPoinTr samples 64 denoising points.")

        if self.subset == "train":
            self.length = int(getattr(config, "NUM_SAMPLES_TRAIN", 4))
        elif self.subset == "val":
            self.length = int(getattr(config, "NUM_SAMPLES_VAL", 10))
        else:
            self.length = int(getattr(config, "NUM_SAMPLES_TEST", 10))

    def __len__(self):
        return self.length

    def _sample_ellipsoid(self, rng, n_points, partial=False):
        points = []
        while sum(chunk.shape[0] for chunk in points) < n_points:
            candidates = rng.normal(size=(max(n_points * 4, 256), 3)).astype(np.float32)
            candidates /= np.linalg.norm(candidates, axis=1, keepdims=True) + 1e-6

            scale = np.array([1.0, 0.72, 0.58], dtype=np.float32)
            candidates = candidates * scale

            if partial:
                # Remove a cap to mimic an incomplete observation.
                candidates = candidates[candidates[:, 0] < 0.55]

            points.append(candidates)

        points = np.concatenate(points, axis=0)[:n_points]
        if self.noise_std > 0:
            points = points + rng.normal(scale=self.noise_std, size=points.shape).astype(np.float32)
        return points.astype(np.float32)

    def __getitem__(self, idx):
        split_offset = {"train": 0, "val": 10000, "test": 20000}.get(self.subset, 30000)
        rng = np.random.RandomState(self.seed + split_offset + idx)

        gt = self._sample_ellipsoid(rng, self.npoints, partial=False)
        partial = self._sample_ellipsoid(rng, self.npartial, partial=True)

        model_id = f"{self.subset}_{idx:04d}"
        return (
            self.taxonomy_id,
            model_id,
            (torch.from_numpy(partial), torch.from_numpy(gt)),
        )
