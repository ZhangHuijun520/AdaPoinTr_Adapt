import argparse
import time
import sys
from pathlib import Path

import torch

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR.parent))

from datasets import build_dataset_from_cfg
from models import build_model_from_cfg
from utils import misc
from utils.config import cfg_from_yaml_file


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default="cfgs/ShapeNet34_models/AdaPoinTr_1gpu_5epoch.yaml",
        help="ShapeNet34 AdaPoinTr config to profile.",
    )
    parser.add_argument("--batch_size", type=int, default=4)
    parser.add_argument("--num_workers", type=int, default=4)
    parser.add_argument("--warmup", type=int, default=2)
    parser.add_argument("--iters", type=int, default=5)
    parser.add_argument("--device", default="cuda:0")
    return parser.parse_args()


def synchronize(device):
    if device.type == "cuda":
        torch.cuda.synchronize(device)


def main():
    args = parse_args()
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for this profiler.")

    device = torch.device(args.device)
    config = cfg_from_yaml_file(args.config)
    dataset = build_dataset_from_cfg(config.dataset.train._base_, config.dataset.train.others)
    loader = torch.utils.data.DataLoader(
        dataset,
        batch_size=args.batch_size,
        shuffle=True,
        drop_last=True,
        num_workers=args.num_workers,
        worker_init_fn=misc.worker_init_fn,
    )

    model = build_model_from_cfg(config.model).to(device)
    model.train()
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4, weight_decay=5e-4)

    npoints = config.dataset.train._base_.N_POINTS
    total_iters = args.warmup + args.iters
    batch_times = []

    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats(device)

    data_iter = iter(loader)
    for idx in range(total_iters):
        try:
            _, _, gt = next(data_iter)
        except StopIteration:
            data_iter = iter(loader)
            _, _, gt = next(data_iter)

        gt = gt.to(device, non_blocking=True)
        partial, _ = misc.seprate_point_cloud(
            gt, npoints, [int(npoints * 1 / 4), int(npoints * 3 / 4)], fixed_points=None
        )
        partial = partial.to(device, non_blocking=True)

        synchronize(device)
        start = time.time()

        ret = model(partial)
        sparse_loss, dense_loss = model.get_loss(ret, gt, 0)
        loss = sparse_loss + dense_loss
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()

        synchronize(device)
        elapsed = time.time() - start
        if idx >= args.warmup:
            batch_times.append(elapsed)

        print(
            f"iter={idx + 1}/{total_iters} "
            f"phase={'warmup' if idx < args.warmup else 'profile'} "
            f"batch_time={elapsed:.4f}s "
            f"loss={loss.item():.6f}"
        )

    peak_gb = torch.cuda.max_memory_allocated(device) / 1024**3
    mean_time = sum(batch_times) / len(batch_times)
    steps_per_epoch = len(dataset) // args.batch_size
    est_epoch_hours = mean_time * steps_per_epoch / 3600

    print("==== summary ====")
    print(f"batch_size: {args.batch_size}")
    print(f"num_workers: {args.num_workers}")
    print(f"profile_iters: {args.iters}")
    print(f"mean_batch_time_sec: {mean_time:.4f}")
    print(f"steps_per_epoch: {steps_per_epoch}")
    print(f"estimated_epoch_hours_no_validation: {est_epoch_hours:.2f}")
    print(f"peak_cuda_memory_gb: {peak_gb:.2f}")


if __name__ == "__main__":
    main()
