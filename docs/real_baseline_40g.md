# Real Baseline Plan Under a 50G Ziqiang Volume

This note is for the current Ziqiang 5000 container state:

```text
/home/jovyan persistent volume: 50G
available space after environment setup: about 33G
repository size: about 192M
adapointr-server Conda env: about 6.2G
```

The `/` filesystem may show hundreds of GB free, but it is container overlay
storage. Treat `/home/jovyan` as the persistent working area.

## Recommendation

Do not start with full Projected-ShapeNet-55/34. It is large, uses `.pcd`
partials, and is not the right first target under a 33G remaining persistent
volume.

Use this order:

1. Completion3D or another compact `.h5/.npy` dataset for a real-data pipeline
   sanity baseline.
2. PCN small subset if you need PCN-style `.pcd` data before expansion.
3. Full PCN AdaPoinTr after requesting more storage or confirming the dataset
   fits comfortably.
4. Projected-ShapeNet only after the full PCN baseline is stable.

## Keep Datasets Outside the Repository

Use `~/datasets` for data and symlink into the repository:

```bash
mkdir -p ~/datasets
cd ~/adapointr_work/PoinTr
mkdir -p data
ln -s ~/datasets/Completion3D data/Completion3D
```

This keeps repository, data, logs, and future model changes easier to manage.

## Completion3D Small AdaPoinTr Baseline

This project provides a conservative config for real-data smoke and small
baseline experiments:

```text
cfgs/Completion3D_models/AdaPoinTr_small.yaml
```

Expected data layout follows `cfgs/dataset_configs/Completion3D.yaml`:

```text
data/Completion3D/Completion3D.json
data/Completion3D/train/partial/<taxonomy_id>/<model_id>.h5
data/Completion3D/train/gt/<taxonomy_id>/<model_id>.h5
data/Completion3D/val/partial/<taxonomy_id>/<model_id>.h5
data/Completion3D/val/gt/<taxonomy_id>/<model_id>.h5
```

Before a long run, create a 1-epoch sanity config on the server:

```bash
cd ~/adapointr_work/PoinTr
cp cfgs/Completion3D_models/AdaPoinTr_small.yaml \
   cfgs/Completion3D_models/AdaPoinTr_small_1epoch.yaml
python - <<'PY'
from pathlib import Path
p = Path("cfgs/Completion3D_models/AdaPoinTr_small_1epoch.yaml")
s = p.read_text().replace("max_epoch : 300", "max_epoch : 1")
p.write_text(s)
PY
```

Run:

```bash
conda activate adapointr-server
python main.py \
  --config cfgs/Completion3D_models/AdaPoinTr_small_1epoch.yaml \
  --exp_name c3d_small_1epoch \
  --num_workers 4 \
  --val_freq 1 \
  2>&1 | tee c3d_small_1epoch.log
```

If this passes, then run the longer config:

```bash
nohup python main.py \
  --config cfgs/Completion3D_models/AdaPoinTr_small.yaml \
  --exp_name c3d_small_baseline \
  --num_workers 4 \
  --val_freq 5 \
  > c3d_small_baseline.log 2>&1 &

tail -f c3d_small_baseline.log
```

## PCN Under Tight Storage

PCN is more relevant as an AdaPoinTr baseline, but full PCN may be tight with
only about 33G free. Also, PCN uses `.pcd`; this project includes a PCD reader
fallback that does not require Open3D when the server lacks `libX11`.

Use PCN in one of these ways:

- Request more persistent storage and run full PCN.
- Create a PCN small subset for a real-data dry run.
- Use PCN Cars only if your immediate goal is a smaller category-limited run.

For a formal paper baseline, prefer full PCN once storage is available.

## Space Hygiene

Check space before and after every dataset/extract/train step:

```bash
df -h ~
du -sh ~/datasets/* 2>/dev/null || true
du -sh ~/adapointr_work/PoinTr/experiments/* 2>/dev/null || true
```

If space gets tight, remove only clearly disposable experiments, not Conda:

```bash
rm -rf ~/adapointr_work/PoinTr/experiments/AdaPoinTr/ToyPCN_models/server_toy_smoke*
```

