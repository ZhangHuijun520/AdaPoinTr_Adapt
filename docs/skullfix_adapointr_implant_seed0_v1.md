# SkullFix AdaPoinTr-Implant Seed-0 Baseline Freeze

## Freeze identity

- Baseline ID and intended Git tag:
  `skullfix-adapointr-implant-seed0-v1`
- Branch at freeze preparation: `feature/skullfix-baseline`
- Training config:
  `cfgs/SkullFix_models/AdaPoinTr_implant_full100_bncal.yaml`
- Input: defective skull point cloud, 8192 points
- Target/output: implant point cloud, 4096 points
- Final reconstruction: defective skull union predicted implant

The machine-readable record is
`docs/baselines/skullfix_adapointr_implant_seed0_v1.json`.

## Data and training protocol

- Source: 100 labeled SkullFix training triplets.
- Case-level split: 80 train, 10 validation, 10 test.
- Split seed: 20260628.
- Model seed: 0.
- Training: 100 epochs, total batch size 8.
- Query selection: `learned_only`.
- Denoising branch: disabled.
- BatchNorm: running statistics reset and recalibrated with all 80 training
  inputs in 10 batches after training.

The test cases are:

```text
001, 092, 047, 014, 000, 030, 079, 054, 056, 053
```

## Checksums

Prepared point-cloud bundle:

```text
da4e3b50acf5d8768cf497bc9b848e4db849ecdc01abeef21e08e7d31d128a3c
```

Final calibrated checkpoint:

```text
6368ea972e8346e2679fdefec9e5c736bd0dbebefb2ed01d45056b2a22108119
```

External baseline archive:

```text
filename: skullfix_adapointr_implant_seed0_v1.tar
size:     394362880 bytes
sha256:   38c8e2cf148b581494e0a3966bb6bcf13198be8f37098941227660b3ab04ba71
verified: true
```

The checkpoint and archive are intentionally excluded from Git.

## Test results

Point-surface implant metrics:

| Metric | Mean |
|---|---:|
| CD-L1 | 2.956 mm |
| HD95 | 6.326 mm |
| NSD at 1 mm | 0.1268 |

Point-sampled rim diagnostics:

| Metric | Mean |
|---|---:|
| Contact-rim CD-L1 | 8.155 mm |
| Contact-rim HD95 | 29.027 mm |
| GT-rim to prediction p95 | 7.625 mm |

Voxelized implant metrics under a fixed 1 mm surface splat:

| Metric | Mean |
|---|---:|
| DSC | 0.2585 |
| Absolute RVE | 0.6630 |
| Surface ASSD | 2.586 mm |
| Surface HD95 | 6.320 mm |
| Surface Dice at 1 mm | 0.3322 |
| Surface Dice at 2 mm | 0.5753 |

Final-reconstruction DSC is 0.9564 versus 0.9541 for the defective input.
The paired mean gain is 0.00236 and its bootstrap confidence interval crosses
zero. Absolute RVE improves from 0.0878 to 0.0603, while tight-tolerance
whole-skull Surface Dice decreases.

## Interpretation and limits

This tag freezes the first reproducible SkullFix AdaPoinTr implant-prediction
baseline. It is suitable as the seed-0 reference for later Mamba experiments.

The 1 mm surface splat underestimates implant volume by about 66 percent, so
voxel DSC is conversion-dependent and must always be reported with the splat
radius. Whole-skull metrics are dominated by unchanged anatomy. Implant and
rim metrics are therefore the primary comparison targets.

Splat-radius sensitivity analysis and additional training seeds may be added
later. They do not change the identity of this frozen seed-0 model and should
receive a later evaluation revision or tag.
