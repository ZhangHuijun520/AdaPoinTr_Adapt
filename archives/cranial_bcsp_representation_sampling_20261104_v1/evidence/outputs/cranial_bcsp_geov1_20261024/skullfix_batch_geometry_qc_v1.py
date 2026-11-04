# -*- coding: utf-8 -*-
"""One local, read-only SkullFix train/validation solid-geometry QC batch."""
import os
os.environ['OMP_NUM_THREADS'] = '2'
os.environ['OPENBLAS_NUM_THREADS'] = '2'
import csv
import gc
import gzip
import hashlib
import importlib.util
import json
import sys
import time
import traceback
from pathlib import Path
import numpy as np
import psutil
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
OUT = BASE / 'skullfix_batch_geometry_qc_20261102_v1'
RAW = Path('E:/dataset/SkullFix/extracted/training_set')
META = Path('E:/dataset/SkullFix/pointcloud_defective_norm')
READER = ROOT / 'outputs/cranial_geometry_diagnostic_20261023/analyze_raw_pairs_v1.py'
START = time.monotonic()
PEAK = 0
CASE_START = START
TIMEOUT = 2700

def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()

def dump(p, x):
    with Path(p).open('x', encoding='utf-8') as f:
        json.dump(x, f, ensure_ascii=False, indent=2, allow_nan=False)

def guard():
    global PEAK
    rss = psutil.Process().memory_info().rss
    PEAK = max(PEAK, rss)
    if rss > 8 * 1024**3:
        raise RuntimeError('monitored RSS exceeds 8 GiB')
    if time.monotonic() - START > TIMEOUT:
        raise RuntimeError('45 minute batch budget exceeded')
    if time.monotonic() - CASE_START > 180:
        raise RuntimeError('180 second case budget exceeded')

spec = importlib.util.spec_from_file_location('skullfix_frozen_reader', READER)
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)

def read_binary(p):
    h, offset, dt, shape, A, o = reader.header(p)
    if not np.isfinite(A).all() or not np.isfinite(o).all():
        raise ValueError('nonfinite physical frame: ' + str(p))
    with p.open('rb') as f:
        f.seek(offset)
        with gzip.GzipFile(fileobj=f) as z:
            payload = z.read(int(np.prod(shape)) * dt.itemsize + 1)
    if len(payload) != int(np.prod(shape)) * dt.itemsize:
        raise ValueError('NRRD payload length: ' + str(p))
    a = np.frombuffer(payload, dtype=dt).reshape(shape, order='F')
    # Validate label values before converting. Do not silently threshold CT.
    minimum, maximum = int(a.min()), int(a.max())
    if minimum != 0 or maximum not in (1, 255):
        raise ValueError('not an accepted binary mask: ' + str(p))
    m = np.asarray(a > 0, order='C')
    if np.count_nonzero(a) != np.count_nonzero(a == maximum):
        raise ValueError('more than two labels: ' + str(p))
    return m, A, o, h.get('space'), [minimum, maximum]

def bbox(m):
    limits = []
    for a in range(3):
        ids = np.flatnonzero(m.any(axis=tuple(b for b in range(3) if b != a)))
        if not len(ids):
            raise ValueError('empty bone mask')
        limits.append([int(ids[0]), int(ids[-1])])
    return limits

def edge_counts(m):
    return [int(np.count_nonzero(np.take(m, v, axis=a)))
            for a in range(3) for v in (0, m.shape[a] - 1)]

def partition(C, D, G):
    overlap = int(np.count_nonzero(D & G))
    mismatch = int(np.count_nonzero(C != (D | G)))
    if overlap or mismatch:
        raise ValueError(f'solid partition mismatch: overlap={overlap}, xor={mismatch}')
    return overlap, mismatch

def boundary_and_interface(D, G, A):
    counts = {'D': 0, 'G': 0}
    interface = []
    hd, hg = hashlib.sha256(), hashlib.sha256()
    area_by_axis = [float(np.linalg.norm(np.cross(A[(a+1)%3], A[(a+2)%3]))) for a in range(3)]
    for a in range(3):
        for sign in (-1, 1):
            guard()
            x, y = reader.shifted_neighbor(D, a, sign)
            for name, m in [('D', D), ('G', G)]:
                # Internal occupied-occupied faces cancel twice; FOV faces remain exposed.
                counts[name] += int(np.count_nonzero(m)) - int(np.count_nonzero(m[x] & m[y]))
            dc = np.argwhere(D[x] & G[y]).astype(np.int32)
            # Query G independently in the reverse direction, using G's own voxel frame.
            gx, gy = reader.shifted_neighbor(G, a, -sign)
            gc_ = np.argwhere(G[gx] & D[gy]).astype(np.int32)
            if sign < 0:
                dc[:, a] += 1
            if sign > 0:
                gc_[:, a] += 1
            kd = 2 * dc
            kg = 2 * gc_
            kd[:, a] += sign
            kg[:, a] -= sign
            if not np.array_equal(kd, kg):
                raise ValueError(f'exact shared face key mismatch axis={a}, sign={sign}')
            # Physical unit normals for the same face must be opposite.
            n = np.cross(A[(a+1)%3], A[(a+2)%3])
            n *= np.sign(np.dot(n, A[a]))
            n = n / np.linalg.norm(n)
            nd, ng = sign*n, -sign*n
            if not np.array_equal(nd, -ng):
                raise ValueError('physical normal mismatch')
            hd.update(np.asarray([a, sign, len(kd)], dtype='<i8').tobytes())
            hg.update(np.asarray([a, sign, len(kg)], dtype='<i8').tobytes())
            hd.update(kd.astype('<i4').tobytes())
            hg.update(kg.astype('<i4').tobytes())
            interface.append({'axis': a, 'D_outward_sign': sign, 'faces': len(kd),
                              'area_mm2': len(kd)*area_by_axis[a],
                              'D_world_normal': nd.tolist(), 'G_world_normal': ng.tolist()})
    if hd.hexdigest() != hg.hexdigest() or sum(x['faces'] for x in interface) == 0:
        raise ValueError('empty or mismatched shared interface')
    return counts, interface, hd.hexdigest()

def contracts():
    C = np.zeros((5, 6, 7), bool)
    C[1:4, 1:5, 1:6] = True
    G = C.copy(); G[:3] = False
    D = C & ~G
    partition(C, D, G)
    A = np.diag([.4, .5, .7])
    counts, faces, _ = boundary_and_interface(D, G, A)
    assert sum(x['faces'] for x in faces) == 20
    assert np.isclose(sum(x['area_mm2'] for x in faces), 7.0)
    assert counts['D'] == 76 and counts['G'] == 58
    bad = D.copy(); bad[3, 2, 2] = True
    try:
        partition(C, bad, G)
    except ValueError:
        pass
    else:
        raise AssertionError('overlap not rejected')
    rotation = np.array([[0., -1., 0.], [1., 0., 0.], [0., 0., 1.]])
    rotated = boundary_and_interface(D, G, A @ rotation)[1]
    assert np.isclose(sum(x['area_mm2'] for x in rotated), 7.0)
    return {'status': 'PASS', 'checks': ['solid complement', 'exact face pairing',
            'anisotropic contact area', 'boundary face counts', 'overlap rejection',
            'rotated physical normals/area']}

def section_image(cid, D, G, A, bounds):
    # Fixed rule for every case, no selection by model performance.
    indices = [int((lo+hi)//2) for lo, hi in bounds]
    spacings = np.linalg.norm(A, axis=1)
    unit = A / spacings[:, None]
    shear = float(np.max(np.abs(unit @ unit.T - np.eye(3))))
    if shear > 1e-5:
        return {'status': 'SKIPPED_NONORTHOGONAL_GRID', 'max_abs_cosine': shear}
    font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 17)
    canvas = Image.new('RGB', (1500, 610), 'white')
    draw = ImageDraw.Draw(canvas)
    draw.text((12, 10), f'SkullFix {cid}: native-grid sections at G bbox midpoints', fill='black', font=font)
    draw.text((12, 35), 'Blue=D; orange=G. Binary segmentation, not CT. Panel axes are voxel directions.', fill='black', font=font)
    for axis in range(3):
        ds = np.take(D, indices[axis], axis=axis)
        gs = np.take(G, indices[axis], axis=axis)
        rgb = np.full((*ds.shape, 3), 245, dtype=np.uint8)
        rgb[ds] = [55, 120, 190]; rgb[gs] = [240, 140, 40]
        remain = [a for a in range(3) if a != axis]
        physical = np.array(ds.shape) * spacings[remain]
        factor = min(470/physical[1], 490/physical[0])
        size = tuple(max(1, int(v)) for v in (physical[1]*factor, physical[0]*factor))
        panel = Image.fromarray(rgb).resize(size, Image.Resampling.NEAREST)
        left = axis*500+(500-size[0])//2
        canvas.paste(panel, (left, 100))
        draw.text((axis*500+12, 73), f'axis {axis} index {indices[axis]} | in-plane mm aspect', fill='black', font=font)
    p = OUT/'sections'/f'{cid}.png'
    if p.exists():
        raise FileExistsError(p)
    canvas.save(p)
    return {'status': 'GENERATED_NOT_ANATOMICAL_CERTIFICATION', 'path': str(p.relative_to(OUT)),
            'fixed_indices': indices, 'max_abs_cosine': shear}

def main():
    global CASE_START
    OUT.mkdir(exist_ok=False)
    (OUT/'cases').mkdir(); (OUT/'sections').mkdir()
    split_path, manifest_path = META/'splits.json', META/'manifest.jsonl'
    split = json.loads(split_path.read_text(encoding='utf-8'))
    sets = {k: set(v) for k, v in split.items()}
    if {k:len(v) for k,v in sets.items()} != {'train':80, 'val':10, 'test':10}:
        raise ValueError('unexpected existing split')
    if any(sets[a] & sets[b] for a,b in [('train','val'),('train','test'),('val','test')]):
        raise ValueError('case identity split overlap')
    records = [json.loads(s) for s in manifest_path.read_text(encoding='utf-8').splitlines() if s.strip()]
    by = {r['case_id']:r for r in records}
    if len(by) != 100 or len(records) != 100 or set(by) != set.union(*sets.values()):
        raise ValueError('manifest identity mismatch')
    selected = sorted(sets['train'] | sets['val'])
    files, mapping = {}, {}
    for cid in selected:
        r = by[cid]
        if r['split'] not in ('train','val') or cid not in sets[r['split']]:
            raise ValueError('manifest split mismatch')
        mapping[cid] = {}
        for role, dirname in [('complete','complete_skull'), ('defective','defective_skull'), ('implant','implant')]:
            rel = Path(dirname)/f'{cid}.nrrd'
            if Path(r['raw'][role]).as_posix() != rel.as_posix():
                raise ValueError('unexpected manifest raw path')
            p = RAW/rel
            if p.is_symlink() or not p.is_file() or not p.resolve().is_relative_to(RAW.resolve()):
                raise ValueError('raw path unavailable/escape/link')
            mapping[cid][role] = str(p)
            files[str(p)] = {'sha256':sha(p), 'bytes':p.stat().st_size}
    inputs = {str(p):sha(p) for p in [Path(__file__), READER, split_path, manifest_path]}
    dump(OUT/'scope.json', {'status':'FROZEN_BEFORE_RAW_PAYLOAD', 'selected_count':90,
         'selected_ids':selected, 'selected_train_ids':sorted(sets['train']),
         'selected_validation_ids':sorted(sets['val']), 'excluded_test_ids':sorted(sets['test']),
         'selection':'existing train+val; no new split or formal future training admission',
         'raw_mapping':mapping, 'raw_files_before':files, 'implementation_metadata_hashes':inputs,
         'budgets':{'batch_seconds':2700, 'per_case_seconds':180, 'monitored_rss_bytes':8*1024**3,
                    'output_bytes':200*1024**2},
         'prohibitions':['no test payload', 'no source modification', 'no new point sampling',
                         'no training/GPU/server', 'no repair or automatic exclusion/retry'],
         'warnings_not_hard_failure':['nonempty FOV contact', 'multiple G components',
                                     'header/manifest coordinate discrepancy'],
         'limitations':['No inner/outer semantic certification; no CT diagnosis',
                        'Exact mask fingerprint only, not near-duplicate patient detection',
                        'Test geometry intentionally unavailable for duplicate comparison']})
    dump(OUT/'synthetic_checks.json', contracts())
    rows, fingerprints = [], {}
    for ix, cid in enumerate(selected):
        CASE_START = time.monotonic(); guard()
        print(f'START {ix+1}/90 {cid}', flush=True)
        path = {k:Path(v) for k,v in mapping[cid].items()}
        C,A,o,space,labels_c = read_binary(path['complete']); guard()
        D,B,b,space_d,labels_d = read_binary(path['defective']); guard()
        G,F,f,space_g,labels_g = read_binary(path['implant']); guard()
        if C.shape != D.shape or C.shape != G.shape:
            raise ValueError(cid + ': shape mismatch')
        if not (np.array_equal(A,B) and np.array_equal(A,F) and np.array_equal(o,b) and np.array_equal(o,f)
                and space == space_d == space_g):
            raise ValueError(cid + ': physical coordinate mismatch')
        partition(C,D,G); guard()
        counts = {k:int(np.count_nonzero(v)) for k,v in [('C',C),('D',D),('G',G)]}
        if any(v == 0 for v in counts.values()):
            raise ValueError(cid + ': empty solid')
        fingerprint = reader.mask_hash(C)
        duplicate = fingerprints.get(fingerprint)
        fingerprints.setdefault(fingerprint, []).append({'case_id':cid,'split':by[cid]['split']})
        boundaries, interface, jhash = boundary_and_interface(D,G,A)
        gb = bbox(G)
        crop = G[tuple(slice(lo,hi+1) for lo,hi in gb)]
        components, ncomp = ndimage.label(crop, ndimage.generate_binary_structure(3,1))
        sizes = np.bincount(components.ravel())[1:]
        largest_fraction = float(sizes.max()/counts['G'])
        del components
        edges = {k:edge_counts(m) for k,m in [('C',C),('D',D),('G',G)]}
        warnings = []
        if any(edges['C']): warnings.append('COMPLETE_BONE_TOUCHES_FOV')
        if any(edges['G']): warnings.append('MISSING_BONE_TOUCHES_FOV')
        if ncomp > 1: warnings.append('G_MULTIPLE_6_CONNECTED_COMPONENTS')
        if duplicate: warnings.append('EXACT_COMPLETE_MASK_DUPLICATE')
        r = by[cid]
        metadata_match = (r['voxel_shape']==list(C.shape) and np.allclose(r['space_directions'], A, rtol=0,atol=1e-10)
                          and np.allclose(r['space_origin'], o, rtol=0,atol=1e-10))
        if not metadata_match: warnings.append('HISTORICAL_MANIFEST_FRAME_DIFFERENCE')
        image = section_image(cid,D,G,A,gb)
        if image['status'].startswith('SKIPPED'): warnings.append('SECTION_NONORTHOGONAL_NOT_RENDERED')
        row = {'case_id':cid,'split':r['split'],'status':'GEOMETRIC_CONTRACT_PASS',
               'shape':list(C.shape),'space':space,'directions_row_vectors':A.tolist(),'origin':o.tolist(),
               'spacing_mm':np.linalg.norm(A,axis=1).tolist(),'voxel_volume_mm3':float(abs(np.linalg.det(A))),
               'binary_values':{'C':labels_c,'D':labels_d,'G':labels_g},'voxels':counts,
               'partition_overlap_voxels':0,'partition_xor_voxels':0,'complete_mask_fingerprint':fingerprint,
               'boundary_faces':boundaries,'shared_J_faces':sum(x['faces'] for x in interface),
               'shared_J_area_mm2':sum(x['area_mm2'] for x in interface),
               'shared_J_canonical_keys_sha256':jhash,'shared_J_pairing_exact':True,
               'shared_J_opposite_physical_normals':True,'interface_by_direction':interface,
               'G_bbox_voxel_indices':gb,'G_FOV_margins_voxels':[[lo,int(C.shape[a]-1-hi)] for a,(lo,hi) in enumerate(gb)],
               'FOV_contact_voxels_axis0low_high_axis1low_high_axis2low_high':edges,
               'G_components_6':int(ncomp),'G_largest_component_fraction':largest_fraction,
               'historical_manifest_frame_matches':bool(metadata_match),'warnings':warnings,'section':image,
               'elapsed_seconds':time.monotonic()-CASE_START}
        dump(OUT/'cases'/f'{cid}.json',row); rows.append(row)
        print(f'DONE {cid} J={row["shared_J_faces"]} components={ncomp} warnings={warnings}',flush=True)
        del C,D,G,crop
        gc.collect(); guard()
    changed = [p for p,v in files.items() if sha(p) != v['sha256']]
    changed_inputs = [p for p,h in inputs.items() if sha(p) != h]
    if changed or changed_inputs:
        raise ValueError('source/implementation changed during batch')
    duplicates = [v for v in fingerprints.values() if len(v)>1]
    cross_split = [v for v in duplicates if len({x['split'] for x in v})>1]
    output_bytes = sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file())
    if output_bytes > 200*1024**2:
        raise RuntimeError('output budget exceeded')
    summary = {'status':'COMPLETED_GEOMETRY_PASS' if not cross_split else 'COMPLETED_GEOMETRY_PASS_SPLIT_BLOCKED',
               'case_count':len(rows),'train_cases':sum(r['split']=='train' for r in rows),
               'validation_cases':sum(r['split']=='val' for r in rows),'test_payload_reads':0,
               'raw_file_count':len(files),'raw_files_hashes_unchanged':True,
               'implementation_metadata_unchanged':True,'exact_duplicate_complete_groups':duplicates,
               'cross_train_validation_duplicate_groups':cross_split,
               'warning_cases':[{ 'case_id':r['case_id'],'warnings':r['warnings']} for r in rows if r['warnings']],
               'elapsed_seconds':time.monotonic()-START,'sampled_RSS_max_bytes':PEAK,
               'output_bytes_before_summary':output_bytes,
               'sections_generated':sum(r['section']['status'].startswith('GENERATED') for r in rows),
               'all_shared_J_faces_exactly_paired':all(r['shared_J_pairing_exact'] for r in rows),
               'all_shared_J_normals_opposite':all(r['shared_J_opposite_physical_normals'] for r in rows),
               'training_gpu_model_calls':0,'new_point_sets':0}
    dump(OUT/'summary.json',summary)
    with (OUT/'case_summary.csv').open('x',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['case_id','split','G_voxels','J_faces','J_area_mm2','G_components6',
                                   'G_largest_component_fraction','C_FOV_contact','G_FOV_contact','warnings'])
        for r in rows:
            e=r['FOV_contact_voxels_axis0low_high_axis1low_high_axis2low_high']
            w.writerow([r['case_id'],r['split'],r['voxels']['G'],r['shared_J_faces'],r['shared_J_area_mm2'],
                        r['G_components_6'],r['G_largest_component_fraction'],any(e['C']),any(e['G']),';'.join(r['warnings'])])
    print(json.dumps(summary,ensure_ascii=False),flush=True)

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    try:
        main()
    except BaseException as exc:
        if OUT.is_dir() and not (OUT/'failure.json').exists():
            dump(OUT/'failure.json',{'status':'FAILED_STOP_NO_RETRY','error_type':type(exc).__name__,
                 'error':str(exc),'traceback':traceback.format_exc(),'elapsed_seconds':time.monotonic()-START})
        traceback.print_exc()
        raise
