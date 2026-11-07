# Cranial-BCSP-Mamba P2 frozen code and results archive

Start with [the complete Chinese report](REPORT_zh.md). P2 completed six new training runs (H1 C/D and H2 AUX/COUPLE C/D), 23,400 updates, 630 new Native predictions, 1,680 frozen-model prefix extractions and two unified CPU score batches. The fixed H1 and H2 candidates did not establish stable complete-bone/interface improvement and are closed. H3 is a draft only, never implemented/trained in P2.

## Public contents

`evidence/` preserves original code, CPU test sources/results, protocols, consumed requests, implementation/P3 records, training metrics, prediction manifests/summaries, saved case/source scores, failure history, formal audits, interpretation and final report. `parent_source_snapshot/` contains the exact inherited model/helper snapshots; original AdaPoinTr SHA256 is 1f3eb07ad0c3e2f78756682dcb273d745939dc7efda5563c6528915d6d89a1d4. Selected inherited P1 and BCSP contract/metric Python sources retain their original paths. `source_file_manifest_v1.json` maps bytes to original local paths; `files.sha256` binds this public payload. Historical absolute paths are provenance, not automatic synchronization or runnable instructions.

The parent publication is annotated tag `cranial-bcsp-mamba-p1-20261106-final`, commit `8c638d04e53b6c2a7dfccef39488875bbcdd532d` in ZhangHuijun520/AdaPoinTr_Adapt. The parent experiment and representation archive remain separate evidence, not new P2 runs.

## Local-only contents and limits

The full local tar additionally holds `local_attachments/`: already downloaded H1/H2 Native predictions, reused M0 C/D predictions and the frozen-feature probe archive. Their hashes appear in `local_attachment_reference_manifest_v1.json`. These binary arrays are NOT published here. All five source archives were hash-checked against sidecars/frozen evidence before copying. The full tar is then streamed back member-by-member and SHA256 checked.

No final model checkpoint, original NRRD/STL/input/reference point datasets, compiled provider, environment or credentials are included. Generated NPZ/PTH fixtures, transport tarballs and unlisted binaries are excluded and inventoried. Exact hashes of six final weights are provenance, NOT proof of local checkpoint backup. This is a code/results archive, not a self-contained inference/retraining environment. Re-scoring also requires the separately bound geometry references. No server file is deleted or modified by this archive.

Single seed/fold, repeated development use and finite native Mamba gradient nondeterminism constrain the conclusions. No p-values, bootstrap, formal gate or clinical certification. Native scores contain no GT registration. Existing requests are consumed historical evidence, not replay authorization. Secret pattern scanning is bounded detection, not a guarantee against all possible sensitive strings.
