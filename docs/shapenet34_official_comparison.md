# ShapeNet-34 Official AdaPoinTr Reproduction Comparison

This note compares the local 4-GPU official ShapeNet-34 AdaPoinTr run with
Table II in the AdaPoinTr TPAMI paper.

## Source

- Paper: `adapointr_paper.pdf`, Table II, "Results on ShapeNet-34".
- Local checkpoint:
  `experiments/AdaPoinTr/ShapeNet34_models/shapenet34_adapointr_official_full_4gpu/ckpt-best.pth`
- Local eval logs:
  `logs/shapenet34_official_eval/`

The paper table reports CD-L2 multiplied by 1000 for simple, moderate, and
hard settings. It reports one F-Score@1% value averaged over the three settings.
It does not report CD-L1 for ShapeNet-34.

## Paper Table II: AdaPoinTr

| Split | CD-S | CD-M | CD-H | CD-L2 Avg | F-Score@1% Avg |
|---|---:|---:|---:|---:|---:|
| 34 seen categories | 0.48 | 0.63 | 1.07 | 0.73 | 0.469 |
| 21 unseen categories | 0.61 | 0.96 | 2.11 | 1.23 | 0.416 |

## Local Run

| Split | Difficulty | F-Score | CD-L1 | CD-L2 |
|---|---|---:|---:|---:|
| seen | easy/simple | 0.4337 | 11.0794 | 0.4736 |
| seen | median/moderate | 0.4186 | 11.9999 | 0.6315 |
| seen | hard | 0.3815 | 14.2977 | 1.0953 |
| unseen | easy/simple | 0.4034 | 11.8139 | 0.5776 |
| unseen | median/moderate | 0.3840 | 13.3681 | 0.9307 |
| unseen | hard | 0.3386 | 17.5877 | 2.0708 |

Local averages over the three difficulty settings:

| Split | CD-L2 Avg | F-Score Avg |
|---|---:|---:|
| seen | 0.7335 | 0.4113 |
| unseen | 1.1930 | 0.3753 |

## Delta Against Paper

Negative CD-L2 delta means the local run is lower/better. Positive F-Score delta
means the local run is higher/better.

| Split | CD-S delta | CD-M delta | CD-H delta | CD-L2 Avg delta | F-Score Avg delta |
|---|---:|---:|---:|---:|---:|
| seen | -0.0064 | +0.0015 | +0.0253 | +0.0035 | -0.0577 |
| unseen | -0.0324 | -0.0293 | -0.0392 | -0.0370 | -0.0407 |

## Interpretation

The CD-L2 reproduction is very close to the paper:

- Seen CD-L2 Avg: local `0.7335` vs paper `0.73`.
- Unseen CD-L2 Avg: local `1.1930` vs paper `1.23`.

The F-Score reproduction is lower:

- Seen F-Score Avg: local `0.4113` vs paper `0.469`.
- Unseen F-Score Avg: local `0.3753` vs paper `0.416`.

For now, treat CD-L2 as successfully reproduced and mark F-Score as a metric
implementation/protocol item to verify before using it as a key paper number.
The local server used the Torch F-Score fallback because Open3D cannot load in
the headless container without `libX11`. The fallback should be mathematically
equivalent in principle, but this difference is worth checking with a small
sample on an Open3D-capable environment.

EMDistance is not comparable in this run because evaluation currently reports
`0.0000` for EMD.

## F-Score Diagnostic

Open3D was initially unavailable on the Ziqiang container because `libX11.so.6`
and `libGL.so.1` were missing. After installing `xorg-libx11` and `libgl` from
conda-forge, Open3D imports successfully. Re-running seen/unseen evaluation
produced the same F-Score values as the Torch fallback, so the F-Score gap is
not caused by the fallback implementation.

Use this script to check whether the paper F-Score corresponds to a different
threshold or averaging protocol:

```bash
cd ~/adapointr_work/PoinTr
conda activate adapointr-server

python tools/diagnose_shapenet34_fscore.py \
  --config cfgs/ShapeNet34_models/AdaPoinTr.yaml \
  --ckpt experiments/AdaPoinTr/ShapeNet34_models/shapenet34_adapointr_official_full_4gpu/ckpt-best.pth \
  --mode easy \
  --max_samples 100 \
  --num_workers 4

python tools/diagnose_shapenet34_fscore.py \
  --config cfgs/ShapeNetUnseen21_models/AdaPoinTr.yaml \
  --ckpt experiments/AdaPoinTr/ShapeNet34_models/shapenet34_adapointr_official_full_4gpu/ckpt-best.pth \
  --mode easy \
  --max_samples 100 \
  --num_workers 4
```

Repeat with `--mode median` and `--mode hard` if the threshold sweep suggests a
clear explanation.

Partial diagnostic results using the first 100 test models and all 8 fixed
viewpoints:

| Split | Mode | CD-L2 x1000 | F@0.010 | F@0.011 | F@0.012 |
|---|---|---:|---:|---:|---:|
| seen | easy | 0.4223 | 0.4505 | 0.5042 | 0.5554 |
| seen | median | 0.5456 | 0.4378 | 0.4906 | 0.5412 |
| seen | hard | 0.9541 | 0.4022 | 0.4521 | 0.5000 |
| unseen | easy | 0.6043 | 0.3830 | 0.4293 | 0.4744 |
| unseen | median | 0.9815 | 0.3628 | 0.4073 | 0.4508 |
| unseen | hard | 2.1238 | 0.3168 | 0.3560 | 0.3948 |

These sweeps show that F-Score is highly sensitive to the distance threshold:
raising the threshold from `0.010` to `0.011` increases F-Score by about
`0.04-0.05`, which is close to the observed gap against the paper. Sample-
weighted and category-weighted averages are close in these diagnostics, so
averaging protocol is unlikely to be the main cause.

The training validation log also rules out checkpoint selection as the main
cause. Among 61 validation records from epoch 0 to 600, the best F-Score epoch
is also the best CD-L2 epoch:

```text
epoch=560 F=0.4164 CDL2=0.6750 CDL1=12.1775
```

Thus, using `ckpt-best.pth` selected by `consider_metric: CDL2` did not miss a
separate F-Score-best checkpoint.
