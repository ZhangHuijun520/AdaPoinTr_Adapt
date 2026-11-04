"""Bounded descriptive geometry study. Reads 9 development/training NPZs only.

No project imports, torch, checkpoint, GPU, regeneration, mesh repair or installs.
Original masks/STLs are missing: raw-surface metrics remain explicitly unavailable.
"""
import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MPLCONFIGDIR'] = str(__import__('pathlib').Path(__file__).parent / 'mpl_cache')
import csv
import hashlib
import json
import socket
import sys
import time
from pathlib import Path
import numpy as np
import scipy
from scipy.spatial import cKDTree
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent
ROOT = Path('/home/jovyan/datasets')
EXPECTED_HOST = 'shu-common-25721452-notebook-n9i64i-0'

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()

def save_json(name, value):
    with (OUT / name).open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)

def stats(a):
    a = np.asarray(a)
    if not len(a):
        return None
    return {k: float(v) for k, v in zip(['min','p25','median','p75','p95','max','mean'],
            [*np.percentile(a, [0,25,50,75,95,100]), np.mean(a)])}

def spacing(points):
    u = np.unique(points, axis=0)
    if len(u) < 2:
        return None
    return stats(cKDTree(u).query(u, k=2, workers=1)[0][:, 1])

def normal_features(points):
    _, ix = cKDTree(points).query(points, k=32, workers=1)
    q = points[ix]
    q = q - q.mean(axis=1, keepdims=True)
    val, vec = np.linalg.eigh(np.einsum('nki,nkj->nij', q, q) / 32)
    valid = (val[:, 1] > 1e-10) & (val[:, 2] > 1e-10)
    n = vec[:, :, 0]
    dot = np.abs(np.einsum('ni,nki->nk', n, n[ix[:, 1:]]))
    angles = np.degrees(np.arccos(np.clip(dot, 0, 1)))
    reliable = valid[:, None] & valid[ix[:, 1:]]
    a = angles[reliable]
    curvature = np.maximum(val[:, 0], 0) / np.maximum(val.sum(axis=1), 1e-15)
    return n, valid, stats(a), stats(curvature[valid]), np.histogram(a, bins=np.arange(0, 91, 10))[0]

def select_cases():
    selected = []
    metadata = []
    for dataset in ['SkullFix', 'SkullBreak']:
        root = ROOT / (dataset + 'PC')
        mf = root / 'manifest.jsonl'
        rows = [json.loads(x) for x in mf.read_text().splitlines() if x.strip()]
        split = root / ('splits.json' if dataset == 'SkullFix' else 'group_splits.json')
        s = json.loads(split.read_text())
        if dataset == 'SkullFix':
            permitted = set(s['train'])
            rows = [r for r in rows if r['case_id'] in permitted and r['split'] == 'train']
        else:
            permitted = set(s['gate']['train'])
            rows = [r for r in rows if r['skull_id'] in permitted and r['official_split'] == 'train' and r['defect_type'] == 'bilateral']
        for r in sorted(rows, key=lambda r: r['case_id'])[:3]:
            selected.append({'dataset': dataset, 'root': str(root), 'record': r})
        metadata += [mf, split, root / 'SHA256SUMS']
    root = ROOT / 'MUG500plusD6Development400_v1'
    mf = root / 'manifest.jsonl'
    rows = [json.loads(x) for x in mf.read_text().splitlines() if x.strip()]
    rows = [r for r in rows if r['d6_partition'] == 'development' and r['defect_type'] == 'ellipsoid_medium']
    selected += [{'dataset': 'MUG500plus', 'root': str(root), 'record': r}
                 for r in sorted(rows, key=lambda r: r['case_id'])[:3]]
    metadata.append(mf)
    assert len(selected) == 9
    return selected, [{'path': str(p), 'sha256': sha(p)} for p in metadata]

def check_hash(item, path, digest):
    if item['dataset'] == 'MUG500plus':
        assert digest == item['record']['derived_case_sha256']
    else:
        lines = (Path(item['root']) / 'SHA256SUMS').read_text().splitlines()
        matches = [line.split()[0] for line in lines if line.split()[-1].lstrip('*./') == item['record']['point_path']]
        assert len(matches) == 1 and digest == matches[0], (path, 'checksum mismatch')

def make_figure(dataset, cid, p, g, center, scale):
    fig, axes = plt.subplots(2, 3, figsize=(13, 8), constrained_layout=True)
    for col, (u, v, w) in enumerate([(0,1,2),(0,2,1),(1,2,0)]):
        ax = axes[0, col]
        ax.scatter(p[:,u], p[:,v], s=.4, color='#777777', alpha=.35, label='Residual skull')
        ax.scatter(g[:,u], g[:,v], s=.5, color='#D55E00', alpha=.5, label='Target implant')
        ax.axvline(center[u], color='#0072B2', lw=.6)
        ax.axhline(center[v], color='#0072B2', lw=.6)
        ax.set_title(f'World {"XYZ"[u]} / {"XYZ"[v]} projection')
        ax = axes[1, col]
        ps = np.abs(p[:,w] - center[w]) <= 1.0
        gs = np.abs(g[:,w] - center[w]) <= 1.0
        ax.scatter(p[ps,u], p[ps,v], s=8, color='#0072B2', label=f'Residual slab n={ps.sum()}')
        ax.scatter(g[gs,u], g[gs,v], s=8, color='#D55E00', label=f'Target slab n={gs.sum()}')
        ax.set_title(f'2-mm slab at {"XYZ"[w]}={center[w]:.1f} mm')
        ax.legend(fontsize=7)
        for row in range(2):
            axes[row,col].set_aspect('equal', adjustable='box')
            axes[row,col].set_xlabel(f'{"XYZ"[u]} (mm)')
            axes[row,col].set_ylabel(f'{"XYZ"[v]} (mm)')
    axes[0,0].legend(fontsize=7)
    fig.suptitle(f'{dataset}: {cid}\nStored point-cloud views only; NOT raw CT/mesh sections', fontsize=12)
    fig.savefig(OUT / (dataset + '_' + cid + '_point_slabs.png'), dpi=160)
    plt.close(fig)

def self_check():
    a = np.array([[0.,0.,0.],[1.,0.,0.],[1.,0.,0.]])
    assert spacing(a)['median'] == 1.0
    assert len(np.unique(a, axis=0)) == 2
    assert int((cKDTree([[0.,0.,0.]]).query([[2.,0.,0.],[2.01,0.,0.]])[0] <= 2).sum()) == 1
    assert stats([]) is None
    assert stats([1,2,3])['median'] == 2
    return {'checks': 5, 'status': 'PASS', 'scope': 'Arithmetic sanity checks, not full validation or P3'}

def main():
    started = time.time()
    assert socket.gethostname() == EXPECTED_HOST and os.getuid() == 1000
    assert OUT == Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_geometry_diagnostic_v1_20261023')
    assert not (OUT / 'results.json').exists()
    sanity = self_check()
    selected, metadata = select_cases()
    save_json('selected_scope.json', {'selection': 'Lexicographically first three distinct training/development sources per dataset; SkullBreak bilateral, MUG ellipsoid_medium; no outcome-based selection', 'cases': selected, 'metadata': metadata, 'tolerances_mm': [1.0,2.0], 'raw_geometry_available': False, 'limitations': 'Original voxel masks unavailable at documented Windows paths; D6 source STL parent directory empty. Do not interpret any point metric as raw-surface coverage.'})
    results = []
    rows = []
    for item in selected:
        r = item['record']
        path = (Path(item['root']) / r['point_path']).resolve(strict=True)
        assert path.is_relative_to(ROOT) and path.suffix == '.npz'
        digest = sha(path)
        check_hash(item, path, digest)
        print('READ', item['dataset'], r['case_id'], flush=True)
        with np.load(path, allow_pickle=False) as z:
            keys = list(z.files)
            assert all(k in z for k in ['partial','implant'])
            cen = np.asarray(z['centroid'] if 'centroid' in z else r['normalization']['centroid'], dtype=float)
            scale = float(z['scale'] if 'scale' in z else r['normalization']['scale'])
            assert scale > 0 and np.isfinite(scale)
            p = np.asarray(z['partial'], dtype=float) * scale + cen
            g = np.asarray(z['implant'], dtype=float) * scale + cen
            stored_rim = np.asarray(z['reference_rim_mask'], dtype=bool) if 'reference_rim_mask' in z else None
        assert p.shape == (8192,3) and g.ndim == 2 and g.shape[1] == 3
        assert np.isfinite(p).all() and np.isfinite(g).all()
        dist = cKDTree(g).query(p, k=1, workers=1)[0]
        rim = dist <= 2.0
        unique = np.unique(p, axis=0)
        nn = cKDTree(unique).query(p, k=2, workers=1)[0][:,1]
        knn_r = cKDTree(unique).query(p, k=17, workers=1)[0][:,-1]
        density = 16 / (np.pi * np.maximum(knn_r, 1e-12)**2)
        normal, valid, angle, curvature, hist = normal_features(p)
        width = np.ptp((g - g.mean(axis=0)) @ np.linalg.svd(g - g.mean(axis=0), full_matrices=False)[2].T, axis=0)
        res = {'dataset': item['dataset'], 'case_id': r['case_id'], 'point_path': str(path), 'sha256_before': digest,
               'npz_keys': keys, 'partial_n': len(p), 'implant_n': len(g), 'partial_unique_n': len(unique),
               'partial_duplicate_fraction': 1-len(unique)/len(p), 'normalization_scale_mm': scale,
               'partial_bbox_extent_mm': np.ptp(p, axis=0).tolist(),
               'global_unique_nn_mm': spacing(p), 'implant_unique_nn_mm': spacing(g),
               'contact_support_2mm_n': int(rim.sum()), 'contact_support_2mm_fraction': float(rim.mean()),
               'contact_support_1mm_n': int((dist <= 1).sum()),
               'contact_to_sparse_target_distance_mm': stats(dist[rim]),
               'rim_to_full_cloud_nn_mm': stats(nn[rim]), 'rim_within_band_unique_nn_mm': spacing(p[rim]),
               'knn16_surface_density_proxy_points_per_mm2': stats(density),
               'rim_knn16_surface_density_proxy_points_per_mm2': stats(density[rim]),
               'pca32_normals_valid_n': int(valid.sum()), 'unsigned_neighbor_normal_angle_deg': angle,
               'normal_angle_hist_0_90_step10': hist.tolist(), 'pca32_curvature_proxy': curvature,
               'implant_pca_extent_mm_not_true_opening_width': width.tolist(),
               'reference_rim_mask_count': None if stored_rim is None else int(stored_rim.sum()),
               'reference_rim_mask_agrees_at_2mm': None if stored_rim is None else bool(np.array_equal(rim, stored_rim)),
               'raw_boundary_voxel_count': None, 'raw_surface_coverage': None,
               'inner_outer_cutwall_labels': 'UNDETERMINED_WITHOUT_RAW_GEOMETRY',
               'source_asset_path': r.get('source_asset_path'), 'source_asset_sha256_expected': r.get('source_asset_sha256'),
               'source_geometry_missing': True, 'mesh_topology': None,
               'sha256_after': sha(path)}
        assert res['sha256_before'] == res['sha256_after']
        if stored_rim is not None:
            assert stored_rim.shape == rim.shape
        make_figure(item['dataset'], r['case_id'], p, g, g.mean(axis=0), scale)
        results.append(res)
        rows.append({'dataset': res['dataset'], 'case_id': r['case_id'], 'partial_n': len(p), 'implant_n': len(g),
                     'duplicate_fraction': res['partial_duplicate_fraction'], 'nn_median_mm': res['global_unique_nn_mm']['median'],
                     'support_2mm_n': int(rim.sum()), 'support_2mm_fraction': float(rim.mean()),
                     'rim_nn_median_mm': None if res['rim_within_band_unique_nn_mm'] is None else res['rim_within_band_unique_nn_mm']['median'],
                     'unsigned_normal_angle_median_deg': angle['median']})
        print('DONE', r['case_id'], 'rim=', int(rim.sum()), flush=True)
    with (OUT / 'point_geometry_per_case.csv').open('x', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    fig, axes = plt.subplots(1,3,figsize=(12,4), constrained_layout=True)
    for i, field in enumerate(['nn_median_mm','support_2mm_fraction','rim_nn_median_mm']):
        for j, d in enumerate(['SkullFix','SkullBreak','MUG500plus']):
            vals = [r[field] for r in rows if r['dataset'] == d and r[field] is not None]
            axes[i].scatter(np.full(len(vals), j), vals, color=['#0072B2','#009E73','#D55E00'][j])
        axes[i].set_xticks([0,1,2], ['SkullFix','SkullBreak','MUG500+'], rotation=15)
        axes[i].set_title(field)
        axes[i].grid(axis='y', alpha=.2)
    fig.suptitle('Descriptive stored-cloud diagnostic: 3 selected sources per dataset')
    fig.savefig(OUT/'point_geometry_summary.png', dpi=160)
    plt.close(fig)
    save_json('results.json', {'status': 'PARTIAL_COMPLETED_RAW_GEOMETRY_MISSING', 'hostname': socket.gethostname(),
              'python': sys.version, 'numpy': np.__version__, 'scipy': scipy.__version__, 'matplotlib': matplotlib.__version__,
              'cpu_sanity_checks': sanity, 'cases': results, 'elapsed_seconds': time.time()-started,
              'source_data_unchanged_by_hash': True, 'model_imports': 0, 'checkpoint_loads': 0, 'gpu_computations': 0,
              'caveats': ['Not raw CT/mesh sections', 'PCA normals are unoriented estimates; not anatomical labels',
                          '2mm band is proximity to a sparse target, not true contact wall',
                          'PCA implant extents are not true defect opening width',
                          'No dataset-level statistical inference from three sources',
                          'Stored NPZ only, not runtime augmentation/FPS or model proxy coordinates']})
    files = sorted(p for p in OUT.iterdir() if p.is_file() and p.suffix in ['.json','.csv','.png','.py','.sh'])
    with (OUT / 'analysis_files.sha256').open('x') as f:
        for p in files:
            f.write(sha(p) + '  ' + p.name + '\n')
    print('PARTIAL_COMPLETED_RAW_GEOMETRY_MISSING', flush=True)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        if not (OUT / 'failure.json').exists():
            save_json('failure.json', {'status': 'STOPPED', 'error_type': type(e).__name__, 'error': str(e)})
        raise
