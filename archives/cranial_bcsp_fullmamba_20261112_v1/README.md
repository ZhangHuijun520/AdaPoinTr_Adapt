# Cranial-BCSP-FullMamba — formally closed round, 2026-11-12

Read [the complete Chinese experiment report](REPORT_zh.md). This round established the attention-free F0 encoder–decoder, performed 30 decoder-only conditional interventions, and evaluated a query-aligned interleaved local-conditioning (LQI) revision. Four new scratch runs (F0 C/D, LQI C/D) each completed 3,900 updates; 420 new Native predictions were scored against frozen T0/M0 references. F0 was not a stable improvement. LQI substantially improved Fold D relative to F0 but introduced serious failures in Fold C. These are closed research candidates, not a certified final method.

## Public code and results

`evidence/` preserves original implementation, tests, protocols, requests/authorizations, static/CPU/CUDA/P3 evidence, training/geometry/resource logs, prediction manifests, case/source scores, diagnostics, seven-case static figures, failed attempts and formal audits. `parent_source_snapshot/` preserves inherited AdaPoinTr/helper sources; selected P1 and BCSP training/metric dependencies retain original paths. The parent publication is `cranial-bcsp-mamba-p2-20261107-v1` (commit 9259190ad252cc0678d2f00f2eb109b8c8289c48); P1 and representation archives remain separate parent evidence.

`source_file_manifest_v1.json` binds exact source bytes to their original paths. `files.sha256` binds the public payload. REPORT_zh.md changes navigation links only; evidence copies retain original bytes and historical status. Historical absolute paths are provenance and do not imply filesystem synchronization or replay authorization.

## Local-only results and weights

The full local archive also includes five existing prediction/diagnostic archives and their sidecars (F0, LQI, reused T0/M0 C/D, and 30-intervention predictions/traces). Every archive member was rehashed without deserializing arrays. Interactive seven-case Plotly HTML is local-only because it embeds point arrays; static PNG figures remain public. `local_attachment_reference_manifest_v1.json` records these files, not their data.

Final checkpoints are excluded from this code/results archive and GitHub. Four exact final epoch99/step3900 F0/LQI C/D weights are handled in a separate local checkpoint archive. Raw NRRD/STL/input/reference datasets, compiled providers and Conda environments are excluded. Thus this archive is not a standalone retraining/inference/re-scoring environment. No server deletion, retraining or re-scoring is performed.

## Scientific limits

One seed, repeatedly used development sets, different training GPU UUID/driver between F0 and LQI, and finite native-Mamba gradient nondeterminism limit causal/reliability claims. No new bootstrap, p-values, formal gate or clinical certification. Conditional sensitivity is not accuracy, and final coarse geometry does not identify the earliest causal source. Future coarse spatial conditioning is a proposal only. Consumed requests are historical evidence, not permission to replay.

Secret-pattern checking found no listed patterns; this is bounded detection, not an unlimited guarantee. Public files are deliberately stored with Git text conversion disabled to retain hashes. Binary prediction archives and checkpoints are not pushed to GitHub.
