# Cranial-BCSP-FullMamba: BCSP-SPCG closure

Read [the comprehensive Chinese report](REPORT_zh.md) and [fixed5 geometry panels](FIGURES.md).

Six G0/G1/G2 x Fold C/D models, 3900 updates each; 630 Native predictions, 1050 scoring rows (630model +420sharedcontrol), preregistered2000 paired-source bootstrap draws per fold. Current fixed local8 candidate is closed: G2 minusG1 E_P95 C +1.527mm, D +1.872mm; newly severe9/7, rescued4/0. C interface coverage gains do not replicate consistently. G1 not promoted. Single seed, exposed development data, D_G0 training-device confounding, finite gradient nondeterminism and missing Memory/probe/index captures remain explicit.

Public: exact code, configs, scalar scores, CSV/JSON, bootstrap index identities, execution/freeze and failure evidence, report, static figures and provenance. Local-only: prediction arrays, initializer/probe bytes, bootstrap NPY matrices, artificial binary fixtures and raw transport captures. All six final checkpoints are separately backed up locally, never uploaded to GitHub. Raw medical datasets, clinical/reference arrays and compiled environments are excluded.

Historical requests/authorization receipts/launchers are inert evidence, not permission to execute. Windows and server paths refer to different filesystems and require explicit rebinding. This is a source/evidence snapshot, not an automatic installer. Annotated tag: cranial-bcsp-spcg-20261117-v1. No server files deleted by archival.
